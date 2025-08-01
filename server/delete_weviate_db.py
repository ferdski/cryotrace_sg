import weaviate

client = weaviate.Client("http://localhost:8080")

client.schema.delete_class("Shipment")
print("✅ Deleted Shipment class")
