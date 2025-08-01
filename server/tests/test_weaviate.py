from openai import OpenAI
import weaviate
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
weaviate_client = weaviate.Client("http://localhost:8080")

# Step 1: Ask a question
#question = "Describe the route and evaporation rate for shipper shipper-ln2-20-0007"
question = "I'm looking for a shipment that took place on or about 2025-04-28.  I'm not sure which unit it was. Include the evaporation data in the output."

# Step 2: Embed the question
embedding = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=question
).data[0].embedding

# Step 3: Query Weaviate
results = weaviate_client.query.get("Shipment", ["shipper_id", "summary_text"]) \
    .with_near_vector({"vector": embedding}) \
    .with_limit(5) \
    .do()

retrieved = results["data"]["Get"]["Shipment"]
context_chunks = [obj["summary_text"] for obj in retrieved]

# Step 4: Assemble prompt
prompt = "Use the following shipment logs to answer the user's question:\n\n"
for i, chunk in enumerate(context_chunks):
    prompt += f"---\n{chunk}\n"
prompt += f"\nQuestion: {question}"

# Step 5: Get LLM response
completion = openai_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant for analyzing cryogenic shipments."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.2
)

answer = completion.choices[0].message.content
print("\n🧠 AI Answer:\n", answer)