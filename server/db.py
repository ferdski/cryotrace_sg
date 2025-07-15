import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# locations table can expand as new cities/locations are needed; this will update the locations table in the MySql DB 
def get_or_create_location_id(cursor, location_name):
    cursor.execute("SELECT id FROM locations WHERE name = %s", (location_name,))
    result = cursor.fetchone()
    if result:
        return result['id']
    else:
        cursor.execute("INSERT INTO locations (name) VALUES (%s)", (location_name,))
        return cursor.lastrowid
