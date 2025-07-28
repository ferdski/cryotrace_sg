import weaviate

client = weaviate.Client("http://localhost:8080")  # Replace with your real URL

response = client.query.get(
    "Shipment",  # Replace with your actual class name
    ["shipper_id", "pickup_time"]
).with_where({
    "path": ["shipper_id"],
    "operator": "Equal",
    "valueString": "shipper-ln2-30-0008"
}).do()

# Print how many trips were returned
trips = response["data"]["Get"]["Shipment"]
print(f"Found {len(trips)} trips for shipper-ln2-30-0008")
for t in trips:
    print(t)
