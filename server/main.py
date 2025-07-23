
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from db import get_connection
from pydantic import BaseModel
from chroma_rag import query_gpt_with_rag, load_or_index_shipments, collection
import os
#  api pickup-events
from fastapi import FastAPI, Query, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import shutil



app = FastAPI()

# Allow React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        load_or_index_shipments()

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
def get_containers():
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
    weight_type: str = Form(...),
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
            shutil.copyfileobj(image_path.filename, buffer)

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
                notes.
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

'''async def create_dropoff_event(request: Request):
    form = await request.form()
    print("🔍 Form keys received:", list(form.keys()))
    print("🔍 Form values:", dict(form)) '''

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



@app.get("/api/shippers/{shipper_id}/routes")
def get_shipper_routes(shipper_id: str):
    print(f"s_id: {shipper_id}")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            m.manifest_id,
            m.shipper_id,
            CONCAT(o.company_name, ', ', o.company_address, ', ', o.city, ', ',  o.state) as Origin, 
            CONCAT(d.company_name, ', ', d.company_address, ', ', d.city, ', ', d.state) as Destination,
            m.scheduled_ship_time,
            m.expected_receive_time,
            pe.actual_departure_at,
            de.actual_receive_time,
            pe.measured_weight_kg,
            de.received_weight_kg
        FROM shipping_manifest m
        LEFT JOIN pickup_event pe ON pe.manifest_id = m.manifest_id
        LEFT JOIN dropoff_event de ON de.manifest_id = m.manifest_id
        JOIN locations o ON m.origin_location_id = o.id
        JOIN locations d ON m.destination_location_id = d.id
        WHERE m.shipper_id = %s
        ORDER BY pe.actual_departure_at ASC;
    """

    cursor.execute(query, (shipper_id,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results




if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)