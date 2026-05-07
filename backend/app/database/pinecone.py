from pinecone import Pinecone

from app.config import settings

_client: Pinecone | None = None


def get_pinecone_client() -> Pinecone:
    global _client
    if _client is None:
        _client = Pinecone(api_key=settings.pinecone_api_key)
    return _client


def get_index():
    client = get_pinecone_client()
    return client.Index(settings.pinecone_index_name)
