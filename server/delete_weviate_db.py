import weaviate

#client = weaviate.Client("http://localhost:8080")  # non-Docker version
client = weaviate.Client("http://weaviate:8080") 

client.schema.delete_class("Shipment")
print("✅ Deleted Shipment class")
