import time
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
from utils import format_shipments_for_prompt, format_shipments_brief, compute_evaporation_volume


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

def build_where_filter(shipper_id: str, cutoff_date: Optional[datetime] = None, direction: str = "after") -> dict:
    operands = [
        {"path": ["shipper_id"], "operator": "Equal", "valueText": shipper_id}
    ]

    if cutoff_date is not None and direction in {"before", "after"}:
        operator = "GreaterThan" if direction == "after" else "LessThan"
        operands.append({
            "path": ["pickup_time"],
            "operator": operator,
            "valueDate": cutoff_date.isoformat() + "Z"
        })

    return {"operator": "And", "operands": operands}

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



@app.get("/api/locations")
def get_users():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM locations")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


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
            m.manifest_id,
            m.shipper_id,

            CONCAT(lp.company_name, ', ', lp.company_address, ', ', lp.city, ', ', lp.state) AS origin,
            CONCAT(ld.company_name, ', ', ld.company_address, ', ', ld.city, ', ', ld.state) AS destination,

            m.scheduled_ship_time,
            m.expected_receive_time,
            m.created_at,

            m.origin_contact_name AS pickup_contact_name,
            pe.actual_departure_at AS pickup_time,
            pe.driver_user_id     AS pickup_user_id,
            pe.measured_weight_kg AS pickup_weight,

            de.actual_receive_time AS dropoff_time,
            de.received_by_user_id AS dropoff_user_id,
            de.received_contact_name AS dropoff_contact_name,
            de.received_weight_kg  AS dropoff_weight,

            CASE
                WHEN pe.measured_weight_kg IS NOT NULL
                AND de.received_weight_kg IS NOT NULL
                AND TIMESTAMPDIFF(SECOND, pe.actual_departure_at, de.actual_receive_time) > 0
                THEN
                (pe.measured_weight_kg - de.received_weight_kg) /
                (TIMESTAMPDIFF(SECOND, pe.actual_departure_at, de.actual_receive_time) / 3600)
                ELSE NULL
            END AS evaporation_rate_kg_per_hour,

            lp.company_name    AS origin_company_name,
            lp.company_address AS origin_company_address,
            lp.city            AS origin_city,
            lp.state           AS origin_state,

            ld.company_name    AS dest_company_name,
            ld.company_address AS dest_company_address,
            ld.city            AS dest_city,
            ld.state           AS dest_state

            FROM shipping_manifest m
            LEFT JOIN pickup_event pe  ON m.manifest_id = pe.manifest_id
            LEFT JOIN dropoff_event de ON m.manifest_id = de.manifest_id
            LEFT JOIN container_weight_event cw_pickup  ON m.manifest_id = cw_pickup.manifest_id  AND cw_pickup.weight_type='pickup'
            LEFT JOIN container_weight_event cw_dropoff ON m.manifest_id = cw_dropoff.manifest_id AND cw_dropoff.weight_type='dropoff'
            LEFT JOIN locations lp ON cw_pickup.location_id = lp.id
            LEFT JOIN locations ld ON cw_dropoff.location_id = ld.id
            WHERE m.shipper_id = %s
            ORDER BY pickup_time DESC;


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
            sm.projected_weight_kg,
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
            m.manifest_id,
            m.shipper_id,

            CONCAT(lp.company_name, ', ', lp.company_address, ', ', lp.city, ', ', lp.state) AS origin,
            CONCAT(ld.company_name, ', ', ld.company_address, ', ', ld.city, ', ', ld.state) AS destination,

            m.scheduled_ship_time,
            m.expected_receive_time,
            m.created_at,

            m.origin_contact_name AS pickup_contact_name,
            pe.actual_departure_at AS pickup_time,
            pe.driver_user_id     AS pickup_user_id,
            pe.measured_weight_kg AS pickup_weight,

            de.actual_receive_time AS dropoff_time,
            de.received_by_user_id AS dropoff_user_id,
            de.received_contact_name AS dropoff_contact_name,
            de.received_weight_kg  AS dropoff_weight,

            CASE
                WHEN pe.measured_weight_kg IS NOT NULL
                AND de.received_weight_kg IS NOT NULL
                AND TIMESTAMPDIFF(SECOND, pe.actual_departure_at, de.actual_receive_time) > 0
                THEN
                (pe.measured_weight_kg - de.received_weight_kg) /
                (TIMESTAMPDIFF(SECOND, pe.actual_departure_at, de.actual_receive_time) / 3600)
                ELSE NULL
            END AS evaporation_rate_kg_per_hour,

            lp.company_name    AS origin_company_name,
            lp.company_address AS origin_company_address,
            lp.city            AS origin_city,
            lp.state           AS origin_state,

            ld.company_name    AS dest_company_name,
            ld.company_address AS dest_company_address,
            ld.city            AS dest_city,
            ld.state           AS dest_state

            FROM shipping_manifest m
            LEFT JOIN pickup_event pe  ON m.manifest_id = pe.manifest_id
            LEFT JOIN dropoff_event de ON m.manifest_id = de.manifest_id
            LEFT JOIN container_weight_event cw_pickup  ON m.manifest_id = cw_pickup.manifest_id  AND cw_pickup.weight_type='pickup'
            LEFT JOIN container_weight_event cw_dropoff ON m.manifest_id = cw_dropoff.manifest_id AND cw_dropoff.weight_type='dropoff'
            LEFT JOIN locations lp ON cw_pickup.location_id = lp.id
            LEFT JOIN locations ld ON cw_dropoff.location_id = ld.id
            WHERE m.shipper_id = %s
            ORDER BY pickup_time DESC;

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
    print(f"query results: {results[0]['destination']}")
    '''print("dest: ", results[1]['dest_company_name'],  results[0]['dest_company_address'],
            results[0]['dest_city'],
            results[0]['dest_state'])'''
    cursor.close()
    conn.close()
    return results


@app.get("/api/manifests")
def get_manifests(filter: str = Query(None), manifestId: str = Query(None)):
    print(f"get Manifests: {filter}, {manifestId}")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)   
    
    if (filter):
        if filter == 'next-id':
            cursor.execute("""
                SELECT
                    MAX(manifest_id) AS last_id 
                    FROM shipping_manifest;
            """)
            results = cursor.fetchall()[0]
            last_id = results["last_id"].rsplit('-')[1] or 0
            next_id = int(last_id) + 1
            next_id = f"MAN-{next_id:06d}"
            print("next manifest id = ", next_id)
            cursor.close()
            conn.close()
            return {"res":next_id}

        else:

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

@app.get("/api/preparations")
def get_preparations(shipperId: str = Query(None)):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if shipperId==None:
        cursor.execute("Select shipper_id FROM preparations;")

    else:
        cursor.execute("Select * FROM preparations where shipper_id=%s;", (shipperId,))

    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

#@app.get("/api/measurements")
#def get_measurements(prep_id):

class ManifestCreateRequest(BaseModel):
    manifest_id: str
    shipper_id: str
    origin_location_id: int
    origin_contact_name: str
    destination_location_id: int
    destination_contact_name: str
    scheduled_ship_time: datetime
    expected_receive_time: datetime
    projected_weight_kg: float
    temperature_c: int
    notes: Optional[str] = None
    created_by_user_id: int
    created_at: datetime
    dev_current_time: datetime


@app.post("/api/create-manifest")
async def create_manifest(request: Request):
    try:
        payload = await request.json()
        manifest_id = payload.get('manifest_id', [])
        # 1. Check if manifest_id already exists (avoid duplicates)
        print(f"get Manifest Id: {manifest_id}")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)   

        # verify that this newly allocated manifest_id isn't already used in the DB
        query = """
            SELECT 1
                FROM shipping_manifest
                WHERE %s
                LIMIT 1;
            """
        cursor.execute(query, (manifest_id,))
        results = cursor.fetchall()
        cursor.close()
        if results:
            print("Error: Manifest ID {manifest_id} is already in use")
            return 
        print(f"Manifests: {results}")


        # 2. Create new manifest object
        manifest = ManifestCreateRequest(
            manifest_id=payload['manifest_id'],              
            shipper_id=payload['shipper_id'],               
            origin_location_id=payload['origin_location_id'],       
            origin_contact_name=payload['origin_contact_name'],     
            destination_location_id=payload['destination_location_id'],  
            destination_contact_name=payload['destination_contact_name'],
            scheduled_ship_time=payload['scheduled_ship_time'],                 
            expected_receive_time=payload['expected_receive_time'],   
            projected_weight_kg=payload['projected_weight_kg'],     
            temperature_c=-196,          
            notes=payload['notes'],                   
            created_by_user_id=payload['created_by_user_id'],      
            created_at=datetime.utcnow(),               
            dev_current_time =datetime.utcnow()   
        )

        params = {
            "manifest_id": manifest.manifest_id,
            "shipper_id": manifest.shipper_id,
            "origin_location_id": manifest.origin_location_id,
            "origin_contact_name": manifest.origin_contact_name,
            "destination_location_id": manifest.destination_location_id,
            "destination_contact_name": manifest.destination_contact_name,
            "scheduled_ship_time": manifest.scheduled_ship_time,   # datetime or str acceptable to connector
            "expected_receive_time": manifest.expected_receive_time,
            "projected_weight_kg": manifest.projected_weight_kg,
            "temperature_c": manifest.temperature_c,
            "notes": getattr(manifest, "notes", None),
            "created_by_user_id": manifest.created_by_user_id,
            "created_at": getattr(manifest, "created_at", datetime.utcnow()),
            "dev_current_time": getattr(manifest, "dev_current_time", datetime.utcnow()),
        }   

        sql = """
        INSERT INTO shipping_manifest (
            manifest_id,
            shipper_id,
            origin_location_id,
            origin_contact_name,
            destination_location_id,
            destination_contact_name,
            scheduled_ship_time,
            expected_receive_time,
            projected_weight_kg,
            temperature_c,
            notes,
            created_by_user_id,
            created_at,
            dev_current_time
        ) VALUES (
            %(manifest_id)s,
            %(shipper_id)s,
            %(origin_location_id)s,
            %(origin_contact_name)s,
            %(destination_location_id)s,
            %(destination_contact_name)s,
            %(scheduled_ship_time)s,
            %(expected_receive_time)s,
            %(projected_weight_kg)s,
            %(temperature_c)s,
            %(notes)s,
            %(created_by_user_id)s,
            %(created_at)s,
            %(dev_current_time)s
        )
        """    
        cursor = conn.cursor(dictionary=True)            
        cursor.execute(sql, params)
        conn.commit()
        results = cursor.fetchall()

        # 4. Return the created manifest
        return {
            "status": "success",
            "manifest": {
                "manifest_id": manifest.manifest_id,
                "shipper_id": manifest.shipper_id,
                "scheduled_ship_time": manifest.scheduled_ship_time,
                "expected_receive_time": manifest.expected_receive_time,
                "notes": manifest.notes,
            }
        }
    except Exception as e:
        print("❌ Dropoff event failed:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


UPLOAD_DIR = "uploads/pickup_photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
@app.post("/api/pickup-events")
async def create_pickup_event(
    manifest_id: str = Form(...),
    measured_weight_kg: float = Form(...),
    weight_type: str = Form(...),
    driver_user_id: int = Form(...),
    photo: UploadFile = File(...), 
    notes:  str = Form("")
):
    try:
        # get manifest info for writing params to database
        conn = get_connection()
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
        """, (manifest_id,))
        results = cursor.fetchall()
        
        origin_location_id = results[0]['origin_location_id']
        origin = results[0]['origin']
        destination_location_id = results[0]['destination_location_id']
        destination = results[0]['destination']
        
        # Generate unique filename with timestamp
        timestamp = datetime.utcnow()
        filename = f"{photo.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save file to disk
        #with open(file_path, "wb") as buffer:
        #    shutil.copyfileobj(photo.file, buffer)

        # Store pickup record in the database

        cursor.execute("""
            INSERT INTO pickup_event (
                manifest_id,
                measured_weight_kg,
                weight_measured_at,
                actual_departure_at,
                driver_user_id,
                image_path,
                notes,
                created_at,
                dev_current_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            manifest_id,
            measured_weight_kg,
            timestamp,  # weight_measured_atarture_at
            timestamp, 
            driver_user_id,
            file_path,
            notes,
            timestamp, 
            timestamp
        ))
        conn.commit()

        # store data in container_weight_event as well
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO container_weight_event (
                manifest_id,
                weight_type,
                event_time,
                location_id,
                recorded_by_user_id,
                weight_kg,
                notes,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            manifest_id,
            weight_type,
            timestamp,  # weight_measured_atarture_at
            origin_location_id, 
            driver_user_id,
            measured_weight_kg,
            notes,
            timestamp
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
        weight_type: str = Form(...),  
        image_path: UploadFile = File(...),
        received_by_user_id: str = Form(...)
    ):

    try:
        conn = get_connection()
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
        """, (manifest_id,))
        results = cursor.fetchall()
        
        origin_location_id = results[0]['origin_location_id']
        origin = results[0]['origin']
        destination_location_id = results[0]['destination_location_id']
        destination = results[0]['destination']

        # Generate unique filename with timestamp
        timestamp = datetime.utcnow()
        #filename = f"{photo.filename}"
        file_path = image_path

        UPLOAD_DIR = "uploads/dropoff_photos"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        # Save the uploaded photo
        timestamp = datetime.utcnow()
        filename = f"{manifest_id}_{timestamp}_{image_path.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        #with open(file_path, "wb") as buffer:
        #    shutil.copyfileobj(image_path.file, buffer)

        # 🚨 Validation: check against manifest destination

        cursor.execute("""
            SELECT origin_location_id FROM shipping_manifest
            WHERE manifest_id = %s
        """, (manifest_id,))

        results = cursor.fetchall()


                # store data in container_weight_event as well
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO container_weight_event (
                manifest_id,
                weight_type,
                event_time,
                location_id,
                recorded_by_user_id,
                weight_kg,
                notes,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            manifest_id,
            weight_type,
            timestamp,  # weight_measured_atarture_at
            received_location_id, 
            received_by_user_id,
            received_weight_kg,
            '',
            timestamp
        ))
        conn.commit()       

        manifest_location_id = results[0]['origin_location_id']
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
                actual_receive_time,k
                received_weight_kg,
                condition_notes,
                image_path,
                received_by_user_id,
                created_at,
                dev_current_time 
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            actual_receive_dt
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
            pe.measured_weight_kg, 
            de.received_weight_kg,
            pe.actual_departure_at,
            de.actual_receive_time,
            (pe.measured_weight_kg - de.received_weight_kg) /
            (TIMESTAMPDIFF(SECOND, pe.actual_departure_at, de.actual_receive_time) / 3600) AS evap_rate,

            CASE
                WHEN pe.measured_weight_kg IS NOT NULL
                    AND de.received_weight_kg IS NOT NULL
                    AND (TIMESTAMPDIFF(SECOND, pe.actual_departure_at, de.actual_receive_time) / 3600) > 0
                THEN
                    (pe.measured_weight_kg - de.received_weight_kg) /
                    (TIMESTAMPDIFF(SECOND, pe.actual_departure_at, de.actual_receive_time) / 3600)
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




from fastapi import Request
from pydantic import BaseModel
from cryotrace_ai_class import CryoTraceAI

from openai import OpenAI
import weaviate
import os

def build_final_prompt(shipments: list[dict], question: str, shipper_id: str) -> str:
    if not shipments:
        return ""

    log_count = len(shipments)

    intro = f"""You are an assistant helping users interpret cryogenic shipment data.

You are given {log_count} shipment logs for shipper ID {shipper_id}.
Each log includes:
- shipment ID
- pickup time and contact
- delivery time and receiver
- transit time in hours
- evaporation rate in kg/hour

You must evaluate all logs individually. Do not skip or summarize entries unless explicitly requested.
Present all shipments using the same format, including timestamp, contact name, transit time, and evaporation rate. Use bullet points or numbering consistently.

"""

    logs = "\n\n".join(
        f"""- ID: {s['shipment_id']}
  Pickup: {s['pickup_time']} by {s['pickup_contact']}
  Dropoff: {s['delivery_time']} to {s['receiver']}
  Transit Time (hrs): {s['transit_time_hours']}
  Evap Rate: {s['evaporation_rate_kg_per_hour']} kg/hr"""
        for s in shipments
    )
  

    return f"""{intro}

Shipment Logs:
{logs}

---

User Question:
{question}

Answer:"""



class AskAIRequest(BaseModel):
    question: str
    shipper_id: str | None = None

@app.post("/api/ask-ai")
async def ask_ai(request: Request):
    body = await request.json()
    question = body.get("prompt") or body.get("question")
    shipper_id = body.get("shipper_id")

    if not question or not shipper_id:
        return {"error": "Missing 'prompt' or 'shipper_id'"}

    # Initialize clients
    weaviate_client = weaviate.Client("http://localhost:8080")
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Fields to retrieve
    fields = [
        "shipper_id", "manifest_id", "origin", "origin_contact",
        "destination", "destination_contact", "pickup_time", "dropoff_time",
        "pickup_weight", "dropoff_weight", "evaporation_rate",
        "scheduled_ship_time", "expected_receive_time", "summary_text", "evaporation_rate"
    ]

    # Parse filter conditions
    cutoff_date, direction = CryoTraceAI.parse_cutoff_date_and_direction(question)
    print(f"🕵️ Parsed: shipper_id={shipper_id}, direction={direction}, cutoff_date={cutoff_date}")

    try:
        filters = build_where_filter(shipper_id=shipper_id, cutoff_date=cutoff_date, direction=direction)
    except Exception as e:
        print(f"⚠️ Error building filters: {e}")
        filters = {"path": ["shipper_id"], "operator": "Equal", "valueText": shipper_id}

    # Determine query mode
    mode = determine_query_mode(question)
    print("🔍 Query mode:", mode)

    # Run query
    if mode == "filter":
        results = build_filter_query(weaviate_client, fields, filters).do()
    else:
        embedding = openai_client.embeddings.create(
            model="text-embedding-3-small", input=question
        ).data[0].embedding

        if mode == "semantic":
            results = build_semantic_query(weaviate_client, fields, embedding).do()
        else:
            results = build_hybrid_query(weaviate_client, fields, embedding, filters).do()

    matches = results["data"]["Get"].get("Shipment", [])
    # de-duplicate entries
    seen = set()
    unique_shipments = []

    for entry in matches:
        key = (entry.get("manifest_id"), entry.get("pickup_time"))
        if key not in seen:
            seen.add(key)
            unique_shipments.append(entry)

    print(f"🧹 Deduplicated: {len(matches)} → {len(unique_shipments)} unique shipments")

    
    shipment_logs = [entry for entry in unique_shipments if entry.get("shipper_id") == shipper_id]


    # Analyze and generate prompt
    analyzer = CryoTraceAI(openai_client, cutoff_date=cutoff_date)
    shipments = analyzer.analyze_shipments(shipment_logs, direction=direction)
    for s in shipments:
        print("📦 Checking:", s.get("manifest_id"), s.get("pickup_time"))

    cutoff_line = ""
    formatted = ""
    if cutoff_date and direction in {"before", "after"}:
        formatted = cutoff_date.strftime("%Y-%m-%d %H:%M:%S UTC")
        cutoff_line = f"Only include shipments with pickup time {direction} {formatted}."


    # Generate answer using GPT

    final_prompt = build_final_prompt(shipments, question, shipper_id)
        
    try:
        print(f"📏 Prompt length: {len(final_prompt)} characters")
        print("🧾 FINAL PROMPT:\n", final_prompt)
        
        start_time = time.time()
        ai_response = analyzer._call_model(final_prompt, model="gpt-3.5-turbo")
        duration = time.time() - start_time
        print("response: ", ai_response)
        print(f"🕒 GPT-3.5 turbo response time: {duration:.2f} seconds")
        
        # If 3.5 fails or gives a fallback message, try GPT-4
        if not ai_response or "does not contain enough information" in ai_response:
            print("↩️ Falling back to GPT-4")
            start_time = time.time()
            ai_response = analyzer._call_model(final_prompt, model="gpt-3.5-turbo")
            duration = time.time() - start_time
            print(f"🕒 GPT-4 response time: {duration:.2f} seconds")
            print("response: ", ai_response)

    except Exception as e:
        print("❌ Error generating AI response:", e)
        ai_response = "The AI failed to generate a response."
        print("response: ", ai_response)


    return {
        "shipments": shipments,
        "count": len(shipments),
        "ai_response": ai_response
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)