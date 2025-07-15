
import mysql.connector
import openai
from chromadb import PersistentClient
import os
from dotenv import load_dotenv
from openai import OpenAI
from chromadb.utils import embedding_functions
import chromadb
from chromadb.config import Settings

# --- Load environment variables ---
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Setup ChromaDB client (with persistence)
from chromadb import PersistentClient

chroma_client = PersistentClient(path="./chroma_data")

# ✅ Create/Open a collection with OpenAI embedding
openai_api_key = os.getenv("OPENAI_API_KEY")
embedding_func = embedding_functions.OpenAIEmbeddingFunction(
    api_key=openai_api_key,
    model_name="text-embedding-3-small"
)
collection = chroma_client.get_or_create_collection(
    name="shipment_records",
    embedding_function=embedding_func
)

# --- Helper: Embed text using OpenAI ---
def get_embeddings(texts: list[str]) -> list[list[float]]:
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [d.embedding for d in response.data]


# --- Load and index shipment records from MySQL ---
def load_or_index_shipments():
    if collection.count() > 0:
        return  # Skip if already populated

    # Connect to MySQL
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Shipment_Records")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    texts, metadatas, ids = [], [], []

    for i, row in enumerate(rows):
        text = (
            f"On {str(row.get('timestamp', ''))}, container {row['container_id']} was in {row['location']} "
            f"for a {row['transit']} event. Weight: {row['weight']} kg. "
            f"Condition: {row.get('condition', 'unknown condition')}."
        )
        texts.append(text)
        timestamp = row.get("timestamp", "")
        if not isinstance(timestamp, str):
            timestamp = str(timestamp)
        metadatas.append({
            "timestamp": timestamp,
            "container_id": row.get("container_id", ""),
            "location": row.get("location", ""),
            "transit": row.get("transit", ""),
            "weight": float(row.get("weight", 0)),
            "user_id": int(row.get("user_id", 0)),
            "condition": row.get("condition", "unknown condition")
        })
        ids.append(f"record-{i}")

    embeddings = get_embeddings(texts)
    collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)

# ✅ OpenAI client (v1.x)
openai_client = OpenAI(api_key=openai_api_key)

# --- Main RAG Query Function ---
# ✅ RAG query logic
def query_gpt_with_rag(user_query: str) -> str:
    # 1. Retrieve relevant documents
    results = collection.query(
        query_texts=[user_query],
        n_results=5
    )
    
    docs = results.get("documents", [[]])[0]
    if not docs:
        return "No relevant shipment records were found."

    context = "\n".join(docs)

    # 2. Format prompt for GPT
    messages = [
        {
            "role": "system",
            "content": "You are a logistics assistant helping interpret cryogenic container shipment logs."
        },
        {
            "role": "user",
            "content": f"Use the following context to answer the question:\n\n{context}\n\nQuestion: {user_query}"
        }
    ]

    # 3. Call OpenAI API
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.3
    )

    return response.choices[0].message.content.strip()