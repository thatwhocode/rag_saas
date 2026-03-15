from services.rag_service import RagService
from qdrant_client import AsyncQdrantClient
from adapters.ollama_adapter import LLMAdapter
from adapters.qdrant_adapter import VectorStoreAdapter
from ollama import AsyncClient
from shared_packages.core.config import QdrantSettings
settings= QdrantSettings() 
class RagServiceFactory:
    def __init__(self, qdrant_url: str, ollama_host: str, embed_model: str, chat_model: str):
        self.qdrant_url = qdrant_url
        self.ollama_host = ollama_host
        self.ollama_embed_model = embed_model
        self.ollama_chat_model = chat_model
        pass

    def __call__(self) -> RagService:

        
        ollama_client= LLMAdapter(AsyncClient(self.ollama_host), embed_model=self.ollama_embed_model, chat_model=self.ollama_chat_model)
        qdrant_client = VectorStoreAdapter(AsyncQdrantClient(self.qdrant_url), settings.QDRANT_COLLECTION)
        
        return RagService(qdrant_client, ollama_client)