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
#weaviate_client = weaviate.Client("http://localhost:8080")  # non-Docker version
weaviate_client = weaviate.Client("http://weaviate:8080") 

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

# Create the Shipment class schema if it doesn't exist
def ensure_shipment_schema():
    # Define the schema for "Shipment"
    schema = {
        "classes": [
            {
                "class": "Shipment",
                "description": "Cryogenic shipment record from CryoTrace",
                "vectorizer": "none",
                "properties": [
                    {"name": "shipper_id", "dataType": ["string"]},
                    {"name": "manifest_id", "dataType": ["string"]},
                    {"name": "origin", "dataType": ["text"]},
                    {"name": "destination", "dataType": ["text"]},
                    {"name": "origin_contact", "dataType": ["string"]},
                    {"name": "destination_contact", "dataType": ["string"]},
                    {"name": "pickup_time", "dataType": ["date"]},
                    {"name": "pickup_user_id", "dataType": ["number"]},
                    {"name": "dropoff_time", "dataType": ["date"]},
                    {"name": "dropoff_user_id", "dataType": ["number"]},
                    {"name": "pickup_weight", "dataType": ["number"]},
                    {"name": "dropoff_weight", "dataType": ["number"]},
                    {"name": "evaporation_rate", "dataType": ["number"]},
                    {"name": "scheduled_ship_time", "dataType": ["date"]},
                    {"name": "expected_receive_time", "dataType": ["date"]},
                    {"name": "summary_text", "dataType": ["text"]},
                    {"name": "origin_company_name", "dataType": ["string"]},
                    {"name": "origin_company_address", "dataType": ["string"]},
                    {"name": "origin_company_city", "dataType": ["string"]},
                    {"name": "origin_company_state", "dataType": ["string"]},
                    {"name": "destination_company_name", "dataType": ["string"]},
                    {"name": "destination_company_address", "dataType": ["string"]},
                    {"name": "destination_company_city", "dataType": ["string"]},
                    {"name": "destination_company_state", "dataType": ["string"]}
                ]
            }
        ]
    }

    # Check if the class already exists
    existing_schema = weaviate_client.schema.get()
    shipment_class = next((cls for cls in existing_schema.get("classes", []) if cls["class"] == "Shipment"), None)
    
    if not shipment_class:
        # Create the schema
        weaviate_client.schema.create(schema)
        print("✅ Shipment class schema created.")
    else:
        print("✅ Shipment class already exists.")

# Ensure the schema exists first
ensure_shipment_schema()

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

# Add new fields (these should already be in the schema, but keeping for compatibility)
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

        lp.company_name AS origin_company,
        lp.company_address AS origin_address,
        lp.city AS origin_city,
        lp.state AS origin_state,

        ld.company_name AS destination_company,
        ld.company_address AS destination_address,
        ld.city AS destination_city,
        ld.state AS destination_state,

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
        pickup_time = row['pickup_time'].strftime("%Y-%m-%dT%H:%M:%SZ")
        dropoff_time = row['dropoff_time'].strftime("%Y-%m-%dT%H:%M:%SZ")

        pickup = row['pickup_time']
        dropoff = row['dropoff_time']
        pickup_weight = float(row['pickup_weight'])
        dropoff_weight = float(row['dropoff_weight'])

        if row['shipper_id'] == 'shipper-ln2-30-0009':
            print()
        # Compute transit duration and evaporation rate
        hours = (dropoff - pickup).total_seconds() / 3600.0
        evap_rate = round((pickup_weight - dropoff_weight) / hours, 4) if hours > 0 else 0.0

        origin = f"{row['origin_company']}, {row['origin_address']}, {row['origin_city']}, {row['origin_state']}"
        destination = f"{row['destination_company']}, {row['destination_address']}, {row['destination_city']}, {row['destination_state']}"

        # Construct summary for embedding
        '''summary = (
            f"🔹 Shipper ID: {row['shipper_id']}\n"
            f"📦 Manifest ID: {row['manifest_id']}\n"
            f"📍 Origin: {row['origin']}\n"
            f"👤 Origin Contact: {row['origin_contact']}\n"
            f"🕓 Pickup Time: {pickup.strftime('%Y-%m-%d %H:%M')}\n"
            f"📍 Destination: {row['destination']}\n"
            f"👤 Destination Contact: {row['destination_contact']}\n"
            f"🕓 Dropoff Time: {dropoff.strftime('%Y-%m-%d %H:%M')}\n"
            f"🕓 Scheduled Ship Time: {row['scheduled_ship_time'].strftime('%Y-%m-%d %H:%M')}\n"
            f"🕓 Expected Receive Time: {row['expected_receive_time'].strftime('%Y-%m-%d %H:%M')}\n"
            f"⏱️ In Transit Duration: {hours:.2f} hours\n"
            f"⚖️ Pickup Weight: {pickup_weight:.2f} kg\n"
            f"⚖️ Dropoff Weight: {dropoff_weight:.2f} kg\n"
            f"💧 Evaporation Rate: {evap_rate:.4f} kg/hour\n"
            f"📍 Origin Company Name: {row['origin_company']}\n"
            f"📍 Origin Company Address: {row['origin_address']}\n"
            f"📍 Origin Company City: {row['origin_city']} \n" 
            f"📍 Origin Company State: {row['origin_state']} \n"           
            f"📍 Destination Company Name: {row['destination_company']}\n"
            f"📍 Destination Company Address: {row['destination_address']}\n"
            f"📍 Destination Company City: {row['destination_city']}\n"
            f"📍 Destination Company State: {row['destination_state']}  \n"                                  
        )'''

        #  shorter version which should still have the desired 
        summary = (
            f"Shipper {row['shipper_id']} ({row['manifest_id']}) was picked up from origin "
            f"by {row['origin_contact']} on {pickup.strftime('%Y-%m-%d %H:%M')} and delivered to "
            f"destination (received by {row['destination_contact']}) on {dropoff.strftime('%Y-%m-%d %H:%M')}. "
            f"Transit time was {hours:.2f} hours. Evaporation rate: {evap_rate:.4f} kg/hour."
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
        shipment_data = {
            "shipper_id": row["shipper_id"],
            "manifest_id": row["manifest_id"],
            "origin": origin,
            "destination": destination,
            "origin_contact": row["origin_contact"],
            "destination_contact": row["destination_contact"],
            "pickup_time": pickup.isoformat() + "Z",
            "dropoff_time": dropoff.isoformat() + "Z",
            "scheduled_ship_time": row["scheduled_ship_time"].isoformat() + "Z",
            "expected_receive_time": row["expected_receive_time"].isoformat() + "Z",
            "pickup_user_id": row["pickup_user_id"],
            "dropoff_user_id": row["dropoff_user_id"],
            "pickup_weight": pickup_weight,
            "dropoff_weight": dropoff_weight,
            "evaporation_rate": evap_rate,
            "origin_company_name": row['origin_company'],
            "origin_company_address": row['origin_address'],
            "origin_company_city": row['origin_city'],
            "origin_company_state": row['origin_state'],
            "destination_company_name": row['destination_company'],
            "destination_company_address": row['destination_address'],
            "destination_company_city": row['destination_city'],
            "destination_company_state": row['destination_state'],
            "summary_text": summary  # used only for semantic vector search
        }

        weaviate_client.data_object.create(
            data_object=shipment_data,        # all your structured fields
            class_name="Shipment",            # the class name in your schema
            vector=embedding                  # your precomputed vector (e.g., from OpenAI)
        )

        # Check if object already exists in Weaviate
        '''if weaviate_client.data_object.exists(uuid_str):
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
            )'''
        print(f"✅ Created: {row['shipper_id']} / {row['manifest_id']}")


    except Exception as e:
        print(f"❌ Error processing {row['shipper_id']} / {row.get('manifest_id')}: {e}")
