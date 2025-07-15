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
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM shippers")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

@app.get("/api/records")
def get_records(filter: str = Query(None), containerId: str = Query(None)):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if filter == "date" and containerId:
        cursor.execute("""
        SELECT * FROM Shipment_Records WHERE container_id = %s ORDER BY timestamp
        """, (containerId,))
    else:
        cursor.execute("SELECT * FROM Shipment_Records")

    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results
