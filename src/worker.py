from celery import Celery
from shared_packages.core.config import RedisSettings
from ollama import AsyncClient
from qdrant_client import AsyncQdrantClient
from adapters.qdrant_adapter import VectorStoreAdapter
from adapters.ollama_adapter import LLMAdapter
from shared_packages.core.config import QdrantSettings, LLMSettings
import asyncio
from uuid import UUID


q_settings = QdrantSettings()
ol_settings = LLMSettings()
redis_settings = RedisSettings()

celery_app = Celery('tasks', broker=redis_settings.REDIS_URL, backend=redis_settings.REDIS_URL)

@celery_app.task(name='process_document_task')
def process_document_task(file_path: str, user_id_str: str):
    async def run():
        # Створюємо клієнтів ВСЕРЕДИНІ активного loop
        ol_client = AsyncClient(host=ol_settings.OLLAMA_URL)
        qd_client = AsyncQdrantClient(url=q_settings.QDRANT_URL)
        
        from adapters.qdrant_adapter import VectorStoreAdapter
        from adapters.ollama_adapter import LLMAdapter
        from src.services.ingestor import IngestionService
        
        ingestion = IngestionService(
            VectorStoreAdapter(qd_client, q_settings.QDRANT_COLLECTION),
            LLMAdapter(ol_client, ol_settings.EMBED_MODEL, ol_settings.CHAT_MODEL)
        )
        await ingestion.process_and_save_document(file_path, UUID(user_id_str))
        return f"File {file_path} processed"

    return asyncio.run(run())
@celery_app.task(bind=True, name='process_document_task')
def process_document_task(self, file_path: str, user_id_str: str):
    try:
        user_id = UUID(user_id_str)
        
        async def run_ingestion():
            from src.services.ingestor import IngestionService
            
            ingestion = IngestionService(VectorStoreAdapter(qdrant_client, q_settings.QDRANT_COLLECTION), LLMAdapter(ol_settings, "nomic-embed-text", "llama3" ))
            await ingestion.process_and_save_document(file_path, user_id)
            return f"Документ {file_path} успішно оброблено"

        result_message = asyncio.run(run_ingestion())
        return {"status": "success", "message": result_message}
        
    except Exception as e:
        return {"status": "error", "detail": str(e)}