import weaviate

weaviate_client = weaviate.Client("http://localhost:8080")

response = weaviate_client.query.get("Shipment", [
    "shipper_id",
    "manifest_id",
    "pickup_time",
    "dropoff_time",
    "scheduled_ship_time",
    "expected_receive_time",
    "origin",
    "destination",
    "origin_contact",
    "destination_contact",
    "evaporation_rate"
]).with_limit(5).do()

for shipment in response["data"]["Get"]["Shipment"]:
    print("\n📦 Shipment:")
    for k, v in shipment.items():
        print(f"  {k}: {v}")
