import asyncio
from uuid import UUID
from celery import Celery
from ollama import AsyncClient
from qdrant_client import AsyncQdrantClient
from adapters.qdrant_adapter import VectorStoreAdapter
from adapters.ollama_adapter import LLMAdapter
from src.chat.services.chat_service import ChatService
from src.db.database import AsyncSessionLocal
from src.services.redis import RedisService
from shared_packages.core.config import (
    RedisSettings, 
    QdrantSettings, 
    LLMSettings
)


qdrant_settings = QdrantSettings()
ollama_settings = LLMSettings()
redis_settings = RedisSettings()
redis  = RedisService(redis_url=redis_settings.REDIS_URL)
qdrant_client = AsyncQdrantClient(url=qdrant_settings.QDRANT_URL)

ollama_client_global = AsyncClient(host=ollama_settings.OLLAMA_URL)


celery_app = Celery(
    'worker', 
    broker=redis_settings.REDIS_URL, 
    backend=redis_settings.REDIS_URL
)

@celery_app.task(name='generate_text_task')
def generate_text_task(prompt_text: str):
    async def chat():
        # Виправлено синтаксис повідомлень
        response = await ollama_client_global.chat(
            model=ollama_settings.CHAT_MODEL, 
            messages=[{'role': 'user', 'content': prompt_text}]
        )
        return response.message.content
    return asyncio.run(chat())

@celery_app.task(bind=True, name='process_document_task')
def process_document_task(self, file_path: str, user_id_str: str):
    try:
        user_id = UUID(user_id_str)
        async def run_ingestion():
            from src.services.ingestor import IngestionService
            
            # Використовуємо глобальні налаштування
            vector_store = VectorStoreAdapter(qdrant_client, qdrant_settings.QDRANT_COLLECTION)
            llm_adapter = LLMAdapter(
                ollama_client_global, 
                ollama_settings.EMBED_MODEL, 
                ollama_settings.CHAT_MODEL
            )
            
            ingestion = IngestionService(vector_store, llm_adapter)
            await ingestion.process_and_save_document(file_path, user_id)
            return f"Документ {file_path} успішно оброблено"

        return {"status": "success", "message": asyncio.run(run_ingestion())}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@celery_app.task(name='rename_chat_automatically_task')
def rename_chat_automatically_task(chat_id_str: str, first_message: str):
    import asyncio
    from uuid import UUID
    from src.chat.repositories.chat_repo import ChatRepository
    from src.chat.repositories.access_repo import AccessRepository 
    from src.chat.repositories.message_repo import MessageRepository

    async def run():
        ol_client = AsyncClient(host=ollama_settings.OLLAMA_URL)
        prompt = f"Summarize this in 3 words max: {first_message}"
        
        response = await ol_client.chat(
            model=ollama_settings.CHAT_MODEL, 
            messages=[{'role': 'user', 'content': prompt}]
        )
        new_title = response.message.content.strip().replace('"', '')

        async with AsyncSessionLocal() as session:
            try:
                chat_repo = ChatRepository(session)
                access_repo = AccessRepository(session)
                message_repo = MessageRepository(session)
                
                service = ChatService(
                    session=session,
                    chat_repo=chat_repo, 
                    access_repo=access_repo, 
                    message_repo=message_repo,
                    redis=redis
                )
                await service.rename_chat(UUID(chat_id_str), new_title)
                
                await session.commit()
                print(f"✅ DB Updated: {chat_id_str} -> {new_title}")
            except Exception as e:
                await session.rollback()
                print(f"❌ DB Error inside Task: {str(e)}")
                raise
        return new_title

    return asyncio.run(run())