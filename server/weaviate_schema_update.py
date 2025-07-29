import weaviate

weaviate_client = weaviate.Client("http://localhost:8080")


def add_shipment_property(name: str, data_type: str, description: str = ""):
    try:
        weaviate_client.schema.property.create(
            "Shipment",
            {
                "name": name,
                "dataType": [data_type],
                "description": description
            }
        )
        
        print(f"✅ Added field: {name}")
    except weaviate.exceptions.UnexpectedStatusCodeException as e:
        if "already in use" in str(e).lower():
            print(f"⚠️ Field already exists: {name}")
        else:
            raise

# Fields to add
add_shipment_property("manifest_id", "string", "Manifest identifier for the shipment")
add_shipment_property("origin", "text", "Formatted pickup location address")
add_shipment_property("destination", "text", "Formatted dropoff location address")
add_shipment_property("origin_contact", "text", "User or driver at pickup")
add_shipment_property("destination_contact", "text", "User who received dropoff")
add_shipment_property("scheduled_ship_time", "date", "Scheduled departure time")
add_shipment_property("expected_receive_time", "date", "Expected delivery time")
