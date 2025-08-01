import weaviate
import json

weaviate_client = weaviate.Client("http://localhost:8080")

query = weaviate_client.query.get("Shipment", ["manifest_id", "pickup_time"]) \
    .with_where({
        "operator": "And",
        "operands": [
            {"path": ["shipper_id"], "operator": "Equal", "valueText": "shipper-ln2-20-0007"},
            {"path": ["pickup_time"], "operator": "GreaterThan", "valueDate": "2025-05-04T00:00:00Z"}
        ]
    }) \
    .with_limit(50)

results = query.do()
for r in results["data"]["Get"]["Shipment"]:
    print(r)



schema = weaviate_client.schema.get()
print(json.dumps(schema, indent=2))

bad = weaviate_client.query.get("Shipment", ["manifest_id", "pickup_time"]).with_where({
    "path": ["manifest_id"],
    "operator": "Equal",
    "valueText": "MAN-000073"
}).do()

print(bad)

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
]).with_limit(500).do()


for shipment in response["data"]["Get"]["Shipment"]:
    print("\n📦 Shipment:")
    if shipment['destination_contact'] is not None and 'Ms. Lee' in shipment['destination_contact']:
        for k, v in shipment.items():
            print(f"  {k}: {v}")
