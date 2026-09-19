import os
import logging
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_qdrant import QdrantVectorStore

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("API_URL")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "nvidia/nemotron-3-embed-1b:free")

# Validate critical environment variables
if not OPENROUTER_API_KEY or not QDRANT_URL or not QDRANT_API_KEY:
    logger.error("Missing critical environment variables in the .env file.")
    raise ValueError("Missing required environment variables (OPENROUTER_API_KEY, QDRANT_URL, QDRANT_API_KEY).")

try:
    # Initialize official OpenAI embeddings configured for OpenRouter
    logger.info("Initializing embeddings client...")
    embeddings = OpenAIEmbeddings(
        model=EMBEDDINGS_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        check_embedding_ctx_length=False
    )

    # Connect to Qdrant Cloud
    logger.info("Connecting to Qdrant Cloud...")
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

    collection_name = "test"

    # Create collection if it doesn't exist
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=2048,  # nvidia/nemotron-3-embed-1b uses 2048 dimensions
                distance=models.Distance.COSINE
            )
        )
        logger.info(f"Collection '{collection_name}' created successfully on Qdrant Cloud!")

    # Create payload index safely (handles cases where it already exists)
    try:
        client.create_payload_index(
            collection_name=collection_name,
            field_name="metadata.source",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
        logger.info("Payload index created for 'metadata.source'.")
    except Exception as index_err:
        logger.warning(f"Payload index might already exist or failed to create: {index_err}")

    # Initialize Qdrant Vector Store
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
    logger.info("Vector store initialized successfully with Qdrant Cloud!")

except Exception as e:
    logger.critical(f"Failed to initialize vector store pipeline: {e}")
    raise e