import json
from typing import Optional
import re
import decimal
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from db import get_connection
from pydantic import BaseModel
import re

import os
#  api pickup-events
from fastapi import FastAPI, Query, File, UploadFile, Form, Request, HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import shutil
from openai import OpenAI
from openai.resources.embeddings import Embeddings
import weaviate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
weaviate_client = weaviate.Client("http://localhost:8080")

app = FastAPI()

# Allow React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_shipper_id_from_question(question: str) -> str | None:
    match = re.search(r"(shipper-ln2-\d+-\d{4})", question, re.IGNORECASE)
    return match.group(1) if match else None


filters = {
    "path": ["shipper_id"],
    "operator": "Equal",
    "valueText": "shipper-ln2-20-0007"
}

def build_where_filter(shipper_id=None, cutoff_date=None):
    operands = []

    if shipper_id:
        operands.append({
            "path": ["shipper_id"],
            "operator": "Equal",
            "valueText": shipper_id
        })

    if cutoff_date:
        operands.append({
            "path": ["pickup_time"],
            "operator": "GreaterThan",
            "valueDate": cutoff_date + "T00:00:00Z"
        })

    if not operands:
        return None

    return operands[0] if len(operands) == 1 else {
        "operator": "And",
        "operands": operands
    }



def build_filter_query(weaviate_client, field_list: list, filters: dict):
    query = weaviate_client.query.get("Shipment", field_list)
    if filters:
        query = query.with_where(filters)
    return query.with_limit(100)


def build_semantic_query(weaviate_client, field_list: list, embedding: list):
    return weaviate_client.query.get("Shipment", field_list) \
        .with_near_vector({"vector": embedding}) \
        .with_limit(25)

def build_hybrid_query(weaviate_client, field_list: list, embedding: list, filters: dict):
    return weaviate_client.query.get("Shipment", field_list) \
        .with_near_vector({"vector": embedding}) \
        .with_where(filters) \
        .with_limit(50)

def determine_query_mode(question: str) -> str:
    """
    Decide if the user question should be handled via:
    - 'filter': structured where-clause
    - 'semantic': vector similarity
    - 'hybrid': combine both
    """
    question = question.lower()

    # Structured identifiers
    if re.search(r"shipper-ln2-\d{2}-\d{4}", question):
        return "filter"
    if "manifest id" in question or re.search(r"man-\d{6}", question, re.IGNORECASE):
        return "filter"

    # Numeric or time-based filtering
    if any(term in question for term in ["greater than", "less than", "more than", "before", "after", "between"]):
        return "filter"

    # Location or contact-based semantics + inference
    if any(term in question for term in ["who", "which", "where", "longest", "shortest", "evaporation", "contact", "trip"]):
        return "semantic"

    # Fallback to hybrid if ambiguous
    return "hybrid"


# ✅ POST /api/reindex – clear & reload vector DB from MySQL
@app.post("/api/reindex")
async def reindex_vectors():
    try:
        print("🧹 Fetching all document IDs...")
        all_ids = collection.get(include=[])["ids"]  # Only get IDs, not embeddings

        print(f"🗑️ Deleting {len(all_ids)} documents...")
        if all_ids:
            collection.delete(ids=all_ids)

        print("🔄 Reloading and re-embedding from MySQL...")


        return {"status": "Reindexing complete."}
    except Exception as e:
        print("❌ Reindexing failed:", e)
        return {"error": str(e)}


class AskRequest(BaseModel):
    query: str

@app.post("/api/ask")
async def ask(request: AskRequest):
    try:
        print(f"🔍 Received query: {request.query}")
        answer = query_gpt_with_rag(request.query)
        print(f"✅ RAG response: {answer}")
        return {"answer": answer}
    except Exception as e:
        print("❌ Error in /api/ask:", repr(e))
        return {"error": str(e)}

@app.get("/api/users")
def get_users():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Users")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

@app.get("/api/containers")
def get_containers():
    print("get Containers")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM shippers")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

@app.get("/api/records")
def get_records(filter: str = Query(None), shipperId: str = Query(None)):
    print(f"records api: {filter}, {shipperId}")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if filter == "date" and shipperId:
        #cursor.execute("""
        #SELECT * FROM shipping_manifest WHERE shipper_id = %s ORDER BY scheduled_ship_time
        #""", (shipperId,))
        cursor.execute("""
        SELECT 
            sm.manifest_id,
            sm.created_at,
            sm.shipper_id,
            sm.scheduled_ship_time,
            CONCAT(lo.city, ', ', lo.state) AS origin,
            CONCAT(ld.city, ', ', ld.state) AS destination,
            sm.projected_weight_kg,
            sm.created_by_user_id,
            sm.notes
            FROM shipping_manifest sm
            JOIN locations lo ON sm.origin_location_id = lo.id
            JOIN locations ld ON sm.destination_location_id = ld.id   
            WHERE sm.shipper_id = %s
            ORDER BY sm.scheduled_ship_time DESC              
        """, (shipperId,))
    elif filter == "manifestid" and shipperId:
        #cursor.execute("""
        #SELECT * FROM shipping_manifest WHERE shipper_id = %s ORDER BY scheduled_ship_time
        #""", (shipperId,))
        cursor.execute("""
        SELECT 
            sm.manifest_id,
            sm.created_at,
            sm.shipper_id,
            sm.scheduled_ship_time,
            CONCAT(lo.city, ', ', lo.state) AS origin,
            CONCAT(ld.city, ', ', ld.state) AS destination,
            sm.projected_weight_kg,
            sm.created_by_user_id,
            sm.notes
            FROM shipping_manifest sm
            JOIN locations lo ON sm.origin_location_id = lo.id
            JOIN locations ld ON sm.destination_location_id = ld.id 
            WHERE sm.shipper_id = %s
            ORDER BY sm.manifest_id DESC              
        """, (shipperId,))        
    elif filter == "location" and shipperId:
        #cursor.execute("""
        #SELECT * FROM shipping_manifest WHERE shipper_id = %s ORDER BY scheduled_ship_time
        #""", (shipperId,))
        cursor.execute("""
        SELECT 
            sm.manifest_id,
            sm.created_at,
            sm.shipper_id,
            sm.scheduled_ship_time,
            CONCAT(lo.city, ', ', lo.state) AS origin,
            CONCAT(ld.city, ', ', ld.state) AS destination,
            sm.projected_weight_kg,
            sm.created_by_user_id,
            sm.notes
            FROM shipping_manifest sm
            JOIN locations lo ON sm.origin_location_id = lo.id
            JOIN locations ld ON sm.destination_location_id = ld.id   
            WHERE sm.shipper_id = %s                       
            ORDER BY origin ASC              
        """, (shipperId,)) 

    elif filter == "all":
        #cursor.execute("""
        #SELECT * FROM shipping_manifest WHERE shipper_id = %s ORDER BY scheduled_ship_time
        #""", (shipperId,))
        cursor.execute("""
        SELECT 
            sm.manifest_id,
            sm.created_at,
            sm.shipper_id,
            sm.scheduled_ship_time,
            CONCAT(lo.city, ', ', lo.state) AS origin,
            CONCAT(ld.city, ', ', ld.state) AS destination,
            sm.projected_weight_kg,
            sm.created_by_user_id,
            sm.notes
            FROM shipping_manifest sm
            JOIN locations lo ON sm.origin_location_id = lo.id
            JOIN locations ld ON sm.destination_location_id = ld.id                      
            ORDER BY manifest_id Desc              
        """)         
    else:
        print("Error in query in api/records")

    results = cursor.fetchall()
    print(f"query results: {results}")
    cursor.close()
    conn.close()
    return results


@app.get("/api/manifests")
def get_manifests(filter: str = Query(None), manifestId: str = Query(None)):
    print(f"get Manifests: {filter}, {manifestId}")
    conn = get_connection()
    
    if (filter):
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                sm.manifest_id,
                sm.shipper_id,
                sm.origin_location_id,
                sm.destination_location_id,
                sm.scheduled_ship_time,
                sm.expected_receive_time,
                sm.created_by_user_id,
                CONCAT(origin.city, ', ', origin.state, ', ', origin.company_name, ' ', origin.company_address) AS origin,
                CONCAT(dest.city, ', ', dest.state, ', ', dest.company_name, ' ', dest.company_address) AS destination
            FROM shipping_manifest sm
            LEFT JOIN locations origin ON sm.origin_location_id = origin.id
            LEFT JOIN locations dest ON sm.destination_location_id = dest.id
            WHERE sm.manifest_id = %s
            ORDER BY sm.manifest_id DESC
        """, (manifestId,))
    else:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT manifest_id FROM shipping_manifest 
            ORDER BY manifest_id DESC             
        """)       

    results = cursor.fetchall()
    #print(f"Manifests: {results}")
    cursor.close()
    conn.close()
    return results




UPLOAD_DIR = "uploads/pickup_photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
@app.post("/api/pickup-events")
async def create_pickup_event(
    manifest_id: str = Form(...),
    measured_weight_kg: float = Form(...),
    driver_user_id: int = Form(...),
    photo: UploadFile = File(...), 
    notes:  str = Form("")
):
    try:
        # Generate unique filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{photo.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

        # Store pickup record in the database
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pickup_event (
                manifest_id,
                measured_weight_kg,
                weight_measured_at,
                actual_departure_at,
                driver_user_id,
                image_path,
                notes,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            manifest_id,
            measured_weight_kg,
            datetime.utcnow(),  # weight_measured_atarture_at
            datetime.utcnow(), 
            driver_user_id,
            filename,
            notes,
            datetime.utcnow(), 
        ))
        conn.commit()

        return {"status": "Pickup event created."}

    except Exception as e:
        print("❌ Pickup event failed:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})




UPLOAD_DIR = "uploads/dropoff_photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# async def create_dropoff_event(request: Request):
#     form = await request.form()
#     print("🔍 Form keys received:", list(form.keys()))
#     print("🔍 Form values:", dict(form))

@app.post("/api/dropoff-events")
async def create_dropoff_event(
        manifest_id: str = Form(...),
        received_location_id: str = Form(...),
        received_contact_name: str = Form(""),
        received_weight_kg: str = Form(...),  
        condition_notes: str = Form(...),
        image_path: UploadFile = File(...),
        received_by_user_id: str = Form(...)
    ):

    try:
        UPLOAD_DIR = "uploads/dropoff_photos"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        # Save the uploaded photo
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{manifest_id}_{timestamp}_{image_path.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        #with open(file_path, "wb") as buffer:
        #    shutil.copyfileobj(image_path.file, buffer)
        conn = get_connection()
        cursor = conn.cursor()

        # 🚨 Validation: check against manifest destination
        cursor.execute("""
            SELECT origin_location_id FROM shipping_manifest
            WHERE manifest_id = %s
        """, (manifest_id,))
        manifest_location_id = cursor.fetchone()[0]

        if not manifest_location_id:
            return JSONResponse(status_code=404, content={"error": "Manifest not found"})

        if manifest_location_id == received_location_id:
            return JSONResponse(
                status_code=422,
                content={"error": "received_location_id must differ from manifest's destination_location_id"}
            )

        # Parse datetime string to proper format
        actual_receive_time = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        actual_receive_dt = datetime.fromisoformat(actual_receive_time)

        # Insert into the database
        cursor.execute("""
            INSERT INTO dropoff_event (
                manifest_id,
                received_location_id,
                received_contact_name,
                actual_receive_time,
                received_weight_kg,
                condition_notes,
                image_path,
                received_by_user_id,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            manifest_id,
            received_location_id,
            received_contact_name,
            actual_receive_dt,
            received_weight_kg,
            condition_notes,
            filename,
            received_by_user_id,
            actual_receive_dt,
        ))
        conn.commit()
        cursor.close()
        conn.close()

        return {"status": "Dropoff event recorded."}

    except Exception as e:
        print("❌ Dropoff event failed:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


def decimal_to_float(d):
    if isinstance(d, decimal.Decimal):
        return float(d)
    return d

@app.get("/api/shippers/{shipper_id}/routes")
async def get_shipper_routes(shipper_id: str):
    print(f"\nshipper routes: s_id: {shipper_id}")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            m.manifest_id,
            m.shipper_id,
            CONCAT(lp.company_name, ', ', lp.company_address, ', ', lp.city, ', ',  lp.state) as Origin, 
            CONCAT(ld.company_name, ', ', ld.company_address, ', ', ld.city, ', ', ld.state) as Destination,
            m.scheduled_ship_time,
            m.expected_receive_time,

            m.origin_contact_name AS contact_name,            
            pe.actual_departure_at AS pickup_time,
            pe.driver_user_id AS pickup_user_id,
            pe.measured_weight_kg AS pickup_weight,
            
            de.received_weight_kg,
            de.actual_receive_time AS dropoff_time,
            de.received_by_user_id  AS dropoff_contact,
            m.destination_contact_name AS contact_name,

            lp.company_name,
            lp.company_address,
            lp.city,
            lp.state,

            de.received_by_user_id AS dropoff_user_id,
            de.received_contact_name AS dropoff_contact,
            de.actual_receive_time AS dropoff_time,
            de.received_weight_kg,

            CASE
                WHEN pe.measured_weight_kg IS NOT NULL
                    AND de.received_weight_kg IS NOT NULL
                    AND TIMESTAMPDIFF(HOUR, pe.actual_departure_at, de.actual_receive_time) > 0
                THEN
                    (pe.measured_weight_kg - de.received_weight_kg) /
                    TIMESTAMPDIFF(HOUR, pe.actual_departure_at, de.actual_receive_time)
                ELSE NULL
            END AS evaporation_rate_kg_per_hour,


            ld.company_name,
            ld.company_address,
            ld.city,
            ld.state            


            FROM shipping_manifest m

            LEFT JOIN pickup_event pe 
                ON m.manifest_id = pe.manifest_id

            LEFT JOIN dropoff_event de 
                ON m.manifest_id = de.manifest_id

            LEFT JOIN container_weight_event cw_pickup 
                ON m.manifest_id = cw_pickup.manifest_id AND cw_pickup.weight_type = 'pickup'

            LEFT JOIN container_weight_event cw_dropoff 
                ON m.manifest_id = cw_dropoff.manifest_id AND cw_dropoff.weight_type = 'dropoff'

            LEFT JOIN locations lp 
                ON cw_pickup.location_id = lp.id

            LEFT JOIN locations ld 
                ON cw_dropoff.location_id = ld.id
            

            WHERE m.shipper_id = %s


    """

    cursor.execute(query, (shipper_id,))
    results = cursor.fetchall()
    # Convert any Decimal fields to float (safely)
    for result in results:
        for key, value in result.items():
            result[key] = decimal_to_float(value)


    print(f"results: {results}")
    cursor.close()
    conn.close()

    return results


# @app.get("/api/ask-ai")
# async def ask_ai(shipper_id: str):
#     print(f"\nshipper routes: s_id: {shipper_id}")
#     conn = get_connection()
#     cursor = conn.cursor(dictionary=True)


# Request schema
class AskAIRequest(BaseModel):
    question: str
    shipper_id: str | None = None




@app.post("/api/ask-ai")
async def ask_ai(req: AskAIRequest):
    question = req.question
    shipper_id = req.shipper_id
    from cryotrace_ai_class import CryoTraceAI
    from utils import extract_cutoff_date_from_question
    from utils import format_shipments_for_prompt
    from openai import OpenAI
    import weaviate

    weaviate_client = weaviate.Client("http://localhost:8080")
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    fields = [
        "shipper_id", "manifest_id", "origin", "origin_contact",
        "destination", "destination_contact", "pickup_time", "dropoff_time",
        "pickup_weight", "dropoff_weight", "evaporation_rate",
        "scheduled_ship_time", "expected_receive_time", "summary_text"
    ]

    # Extract date if possible from the user’s question
    cutoff_date = extract_cutoff_date_from_question(question)
    print("🕵️ Parsed cutoff date:", cutoff_date)

    mode = determine_query_mode(question)
    filters = build_where_filter(shipper_id=shipper_id, cutoff_date=cutoff_date)    
    print("🔍 Final Weaviate filters:", filters)

    if mode == "filter":
        results = build_filter_query(weaviate_client, fields, filters).do()
    elif mode == "semantic":
        embedding = openai_client.embeddings.create(
            model="text-embedding-3-small", input=question
        ).data[0].embedding
        results = build_semantic_query(weaviate_client, fields, embedding).do()
    else:
        embedding = openai_client.embeddings.create(
            model="text-embedding-3-small", input=question
        ).data[0].embedding
        results = build_hybrid_query(weaviate_client, fields, embedding, filters).do()

    matches = results["data"]["Get"].get("Shipment", [])
    #shipment_logs = [entry["summary_text"] for entry in matches]
    shipment_logs = [entry for entry in matches if entry.get("shipper_id") == shipper_id]

    # Create analyzer with that cutoff
    analyzer = CryoTraceAI(openai_client, cutoff_date=cutoff_date)
   

    shipments = analyzer.analyze_shipments(shipment_logs)
    print(f"🧪 {len(shipment_logs)} logs returned from Weaviate")
    for log in shipment_logs:
        print("------")
        print(log)

    prompt = f"""You are an assistant helping users interpret cryogenic shipment data.

            Use the logs below to answer the user's question. Provide a clear and structured response with bullet points, timestamps, names, and numeric values when possible.
            Only base your answer on the shipment logs provided. Do not infer or speculate beyond them.
            If the question is unclear or outside the scope of the shipment logs, respond with: "The provided shipment data does not contain enough information to answer that."
            Shipment Logs:
            {format_shipments_for_prompt(shipments)}

            User Question:
            {question}

            Answer:"""

                
    return {
        "shipments": shipments,
        "count": len(shipments)
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)