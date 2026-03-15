import uuid
from qdrant_client import models, AsyncQdrantClient
from uuid import UUID
class VectorStoreAdapter:
    def __init__(self, client: AsyncQdrantClient, collection_name :str):
        self.client = client
        self.collection_name = collection_name
    async def ensure_collection_exists(self):
        exists = await self.client.collection_exists(self.collection_name)
        
        if not exists:
            print(f"🚀 Створюю колекцію {self.collection_name}...")
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=768, 
                    distance=models.Distance.COSINE
                )
            )

    async def search_context(self, query_vector: list[float], user_id : UUID, limit: int = 5) -> list[str]:
        response = await self.client.query_points(
        collection_name=self.collection_name,
        query=query_vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=str(user_id))
                )
            ]
        ),
        limit=limit
    )
        return [point.payload["text"] for point in response.points]
    async def save_chunks(self, chunks: list[str], vectors: list[list[float]], user_id :UUID):
        if not await self.client.collection_exists(self.collection_name):
           await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE))

        points = []
        for chunk, vector in zip(chunks, vectors):
            point = models.PointStruct(
                id=str(uuid.uuid4()), 
                vector=vector,
                payload={
                    "text": chunk,
                    "user_id":str(user_id) ,
                    "source": "CV"
                }
            )
            points.append(point)
        await self.client.upsert(collection_name=self.collection_name, points = points)