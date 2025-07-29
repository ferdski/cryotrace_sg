import os
from dotenv import load_dotenv
from datetime import datetime
import mysql.connector

from openai import OpenAI
import weaviate
import uuid
import hashlib


# Load environment variables
load_dotenv()

# OpenAI client
openai_client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Weaviate client (older syntax)
weaviate_client = weaviate.Client("http://localhost:8080")

def to_rfc3339(dt) -> str:
    """
    Converts a naive or aware datetime object to RFC3339-compliant string.
    Assumes UTC if datetime is naive.
    """
    if not dt:
        return None

    if dt.tzinfo is None:
        # Assume UTC and append 'Z'
        return dt.isoformat() + "Z"
    else:
        # Already timezone-aware — use isoformat (includes offset)
        return dt.isoformat()

def generate_uuid_for_shipment(shipper_id: str, manifest_id: str) -> str:
    unique_key = f"{shipper_id}::{manifest_id}"
    return str(uuid.UUID(hashlib.md5(unique_key.encode()).hexdigest()))

# Add fields to Weaviate schema if they don't exist yet
def ensure_weaviate_field(name: str, data_type: str = "text"):
    existing_schema = weaviate_client.schema.get()
    shipment_class = next((cls for cls in existing_schema["classes"] if cls["class"] == "Shipment"), None)

    if shipment_class:
        existing_fields = {prop["name"] for prop in shipment_class["properties"]}
        if name in existing_fields:
            print(f"⚠️ Field already exists: {name}")
            return

    # Otherwise, create the property
    prop = {
        "name": name,
        "dataType": ["text"] if data_type == "text" else ["date"],
    }
    weaviate_client.schema.property.create("Shipment", prop)
    print(f"✅ Added field: {name}")

# Add new fields
ensure_weaviate_field("origin")
ensure_weaviate_field("destination")
ensure_weaviate_field("scheduled_ship_time", data_type="date")
ensure_weaviate_field("expected_receive_time", data_type="date")
ensure_weaviate_field("origin_contact")
ensure_weaviate_field("destination_contact")

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
        m.origin_contact_name AS origin_contact,
        pe.actual_departure_at AS pickup_time,
        pe.driver_user_id AS pickup_user_id,
        pe.measured_weight_kg AS pickup_weight,
        de.received_weight_kg AS dropoff_weight,
        de.actual_receive_time AS dropoff_time,
        de.received_by_user_id AS dropoff_user_id,
        de.received_contact_name AS destination_contact
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

        # create UUID from shipper_id and manifest_id
        uuid_str = generate_uuid_for_shipment(row["shipper_id"], row["manifest_id"])

        # Get embedding from OpenAI
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=summary
        )
        embedding = embedding_response.data[0].embedding

        # Insert into Weaviate
        shipment_data={
                "manifest_id": row['manifest_id'],
                "shipper_id": row["shipper_id"],
                "pickup_time": to_rfc3339(pickup),
                "dropoff_time": to_rfc3339(dropoff),
                "pickup_weight": pickup_weight,
                "dropoff_weight": dropoff_weight,
                "evaporation_rate": evap_rate,
                "summary_text": summary,
                "origin": row["Origin"],
                "destination": row["Destination"],
                "scheduled_ship_time": to_rfc3339(row["scheduled_ship_time"])  if row["scheduled_ship_time"] else None,
                "expected_receive_time": to_rfc3339(row["expected_receive_time"]) if row["expected_receive_time"] else None,
                "destination_contact": row['destination_contact'],
                "origin_contact": row['origin_contact']
            }

        # Check if object already exists in Weaviate
        if weaviate_client.data_object.exists(uuid_str):
            weaviate_client.data_object.update(
                uuid=uuid_str,
                class_name="Shipment",
                data_object=shipment_data
            )
            print(f"🔁 Updated: {row['shipper_id']} / {row['manifest_id']}")
        else:
            weaviate_client.data_object.create(
                data_object=shipment_data,
                class_name="Shipment",
                uuid=uuid_str,
                vector=embedding
            )
            print(f"✅ Created: {row['shipper_id']} / {row['manifest_id']}")


        print(f"✅ Inserted: {row['shipper_id']}")

    except Exception as e:
        print(f"❌ Error processing {row['shipper_id']} / {row.get('manifest_id')}: {e}")
