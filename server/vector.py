import os
import requests
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_qdrant import QdrantVectorStore

load_dotenv()  # Loads variables from your .env file

API_URL = os.getenv("API_URL")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


# Custom Embeddings wrapper using requests to avoid format mismatches
class OpenRouterRequestsEmbeddings(Embeddings):
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key
        self.url = "https://openrouter.ai/api/v1/embeddings"

    def _call_api(self, texts: list[str]) -> list[list[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "input": texts
        }
        response = requests.post(self.url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        # Sort by index to maintain original document order
        sorted_data = sorted(result["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._call_api(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._call_api([text])[0]

# Initialize custom OpenRouter embeddings with Nvidia Nemotron
embeddings = OpenRouterRequestsEmbeddings(
    model="nvidia/nemotron-3-embed-1b:free",  
    api_key=API_URL
)

# Connect to Qdrant Cloud using URL and API Key
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

# Create collection if it doesn't exist
if not client.collection_exists("test"):
    client.create_collection(
        collection_name="test",
        vectors_config=models.VectorParams(
            size=2048,  # nvidia/nemotron-3-embed-1b uses 2048 dimensions
            distance=models.Distance.COSINE
        )
    )
    print("Collection 'test' created successfully on Qdrant Cloud with dimension 2048!")
    
client.create_payload_index(
    collection_name="test",
    field_name="metadata.source",
    field_schema=models.PayloadSchemaType.KEYWORD
)
print("Payload index created for 'metadata.source'!")

vector_store = QdrantVectorStore(
    client=client,
    collection_name="test",
    embedding=embeddings,
)
print("Vector store initialized successfully with Qdrant Cloud!")