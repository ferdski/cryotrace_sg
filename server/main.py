
import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from db import get_connection
from pydantic import BaseModel
from chroma_rag import query_gpt_with_rag, load_or_index_shipments, collection
import os

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
def get_manifests(filter: str = Query(None), shipperId: str = Query(None)):
    print(f"get Manifests: {filter}, {shipperId}")
    conn = get_connection()
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)