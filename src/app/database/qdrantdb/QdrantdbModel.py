from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from src.helper.config import get_settings , Settings
class QdrantdbModel:
    def __init__(self,qdrant_client: AsyncQdrantClient):
        self.qdrant_client = qdrant_client
        self.settings: Settings = get_settings()
        
    async def create_collection_if_not_exists(self,collection_name: str, vector_size: int):
        """Create a collection in Qdrant if it does not already exist."""
        collections = await self.qdrant_client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)
        if not exists:
            await self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=self.settings.DISTANCE_METRIC
                )
            )
    
    async def upsert_points(self, collection_name: str, vectors: list[list[float]], payloads: list[dict], ids: list[str]):
        """Upsert points into the specified collection."""
        points = [
            PointStruct(
                id=id,
                vector=vector,
                payload=payload
            )
            for id, vector, payload in zip(ids, vectors, payloads)
        ]
        await self.qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )
    
    async def search(self, collection_name: str, query_vector: list[float], chat_id: str, limit: int=10):
        """Search for similar points in the specified collection based on the query vector and chat_id filter."""
        
        filtter_chat_id = Filter(
            must=[
                FieldCondition(
                    key="chat_id",
                    match=MatchValue(value=chat_id)
                )
            ]
        )
        search_result = await self.qdrant_client.query_points(
            collection_name=collection_name,
            query_filter=filtter_chat_id,
            query=query_vector,
            limit=limit
        )
        return search_result # that will return a list of points with their payloads and distances
        