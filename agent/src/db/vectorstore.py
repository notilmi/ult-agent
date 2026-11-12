import logging
from typing import List, Optional, Tuple
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy
from src.config import (
    GEMINI_API_KEY,
    EMBEDDING_MODEL,
    TOP_K_DOCUMENTS,
    SIMILARITY_SCORE_THRESHOLD,
)
from src.db.client import get_connection_string

logger = logging.getLogger(__name__)

COLLECTION_NAME = "ult_knowledge_base"

def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Instantiates GoogleGenerativeAIEmbeddings with Gemini Embedding 2."""
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY,
    )

def get_vectorstore() -> Optional[PGVector]:
    """Instantiates the PGVector vectorstore connected to NeonDB."""
    connection_url = get_connection_string()
    if not connection_url:
        logger.warning("NEON_DATABASE_URL is not set. Vector store unavailable.")
        return None

    try:
        embeddings = get_embeddings()
        vectorstore = PGVector(
            embeddings=embeddings,
            collection_name=COLLECTION_NAME,
            connection=connection_url,
            distance_strategy=DistanceStrategy.COSINE,
            use_jsonb=True,
        )
        return vectorstore
    except Exception as e:
        logger.error(f"Failed to connect to PGVector on NeonDB: {e}")
        return None

def search_documents(
    query: str,
    k: int = TOP_K_DOCUMENTS,
    category: Optional[str] = None,
) -> List[Tuple[Document, float]]:
    """
    Performs cosine similarity search against NeonDB.
    Returns list of (Document, score) where score is similarity (higher = more relevant).
    """
    store = get_vectorstore()
    if store is None:
        logger.warning("Vectorstore is not initialized. Returning empty search results.")
        return []

    filter_dict = {}
    if category and category not in ["general", "unknown", "complaints"]:
        filter_dict["category"] = category

    try:
        # langchain_postgres similarity_search_with_score returns (doc, distance)
        # For DistanceStrategy.COSINE, distance is in [0, 2], lower is closer.
        # Relevance similarity ~ 1.0 - (distance / 2.0) or 1.0 - distance
        raw_results = store.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict if filter_dict else None,
        )

        results = []
        for doc, distance in raw_results:
            # Normalize cosine distance to similarity score [0, 1]
            similarity = max(0.0, 1.0 - float(distance))
            results.append((doc, similarity))

        return results
    except Exception as e:
        logger.error(f"Error during vector search in NeonDB: {e}")
        return []
