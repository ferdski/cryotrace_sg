# create_weaviate_schema.py

import weaviate
import uuid
import hashlib

client = weaviate.Client("http://localhost:8080")



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

                # 🆕 Structured Origin Fields
                {"name": "origin_company", "dataType": ["string"]},
                {"name": "origin_address", "dataType": ["string"]},
                {"name": "origin_city", "dataType": ["string"]},
                {"name": "origin_state", "dataType": ["string"]},

                # 🆕 Structured Destination Fields
                {"name": "destination_company", "dataType": ["string"]},
                {"name": "destination_address", "dataType": ["string"]},
                {"name": "destination_city", "dataType": ["string"]},
                {"name": "destination_state", "dataType": ["string"]},

                # 🆕 Combined Semantic Strings
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
                {"name": "summary_text", "dataType": ["text"]}
            ]
        }
    ]
}


# Check and create schema
if not client.schema.contains(schema):
    client.schema.create(schema)
    print("✅ Weaviate schema created.")
else:
    print("✅ Weaviate schema already exists.")
