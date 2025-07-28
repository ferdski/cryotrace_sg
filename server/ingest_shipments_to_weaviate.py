import os
from dotenv import load_dotenv
from datetime import datetime
import mysql.connector

from openai import OpenAI
import weaviate

# Load environment variables
load_dotenv()

# OpenAI client
openai_client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Weaviate client (older syntax)
weaviate_client = weaviate.Client("http://localhost:8080")

# Connect to MySQL
db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = db.cursor(dictionary=True)

# SQL Query
query = """
    SELECT
        m.manifest_id,
        m.shipper_id,
        CONCAT(lp.company_name, ', ', lp.company_address, ', ', lp.city, ', ',  lp.state) as Origin, 
        CONCAT(ld.company_name, ', ', ld.company_address, ', ', ld.city, ', ', ld.state) as Destination,
        m.scheduled_ship_time,
        m.expected_receive_time,
        pe.actual_departure_at AS pickup_time,
        pe.driver_user_id AS pickup_user_id,
        pe.measured_weight_kg AS pickup_weight,
        de.received_weight_kg AS dropoff_weight,
        de.actual_receive_time AS dropoff_time,
        de.received_by_user_id AS dropoff_user_id
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
"""

cursor.execute(query)
rows = cursor.fetchall()

for row in rows:
    try:
        pickup = row['pickup_time']
        dropoff = row['dropoff_time']
        pickup_weight = float(row['pickup_weight'])
        dropoff_weight = float(row['dropoff_weight'])

        # Compute transit duration and evaporation rate
        hours = (dropoff - pickup).total_seconds() / 3600.0
        evap_rate = round((pickup_weight - dropoff_weight) / hours, 4) if hours > 0 else 0.0

        # Construct summary for embedding
        summary = (
            f"Shipper {row['shipper_id']} was picked up on {pickup.strftime('%Y-%m-%d %H:%M')} "
            f"and dropped off on {dropoff.strftime('%Y-%m-%d %H:%M')}, in transit for {hours:.2f} hours. "
            f"Evaporation rate was {evap_rate:.4f} kg/hour."
        )

        # Get embedding from OpenAI
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=summary
        )
        embedding = embedding_response.data[0].embedding

        # Insert into Weaviate
        weaviate_client.data_object.create(
            data_object={
                "shipper_id": row["shipper_id"],
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
                "pickup_weight": pickup_weight,
                "dropoff_weight": dropoff_weight,
                "evaporation_rate": evap_rate,
                "summary_text": summary
            },
            class_name="Shipment",
            vector=embedding
        )

        print(f"✅ Inserted: {row['shipper_id']}")

    except Exception as e:
        print(f"❌ Error processing {row['shipper_id']}: {e}")
