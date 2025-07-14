from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from db import get_connection

app = FastAPI()

# Allow React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    cursor.execute("SELECT * FROM Containers")
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
