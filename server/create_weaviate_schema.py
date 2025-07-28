# create_weaviate_schema.py

import weaviate

client = weaviate.Client("http://localhost:8080")

# Define the schema for "Shipment"
schema = {
    "classes": [
        {
            "class": "Shipment",
            "description": "Cryogenic shipment record from CryoTrace",
            "vectorizer": "none",  # We're using OpenAI manually
            "properties": [
                {
                    "name": "shipper_id",
                    "dataType": ["string"],
                    "description": "Unique container ID"
                },
                {
                    "name": "pickup_time",
                    "dataType": ["date"]
                },
                {
                    "name": "dropoff_time",
                    "dataType": ["date"]
                },
                {
                    "name": "pickup_weight",
                    "dataType": ["number"]
                },
                {
                    "name": "dropoff_weight",
                    "dataType": ["number"]
                },
                {
                    "name": "evaporation_rate",
                    "dataType": ["number"],
                    "description": "Nitrogen loss rate in kg/hour"
                },                
                {
                    "name": "summary_text",
                    "dataType": ["text"],
                    "description": "Natural language summary for semantic search"
                }
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
