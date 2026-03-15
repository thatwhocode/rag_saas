from src.chat.repositories.chat_repo import ChatRepository
from src.chat.repositories.access_repo import AccessRepository
from src.chat.repositories.message_repo import MessageRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.exceptions import AccessDeniedException
from src.services.redis import RedisService
import asyncio
import uuid
class ChatService():
    def __init__(self,session : AsyncSession, chat_repo : ChatRepository, access_repo : AccessRepository, message_repo : MessageRepository, redis : RedisService):
        self.chat_repo = chat_repo
        self.access_repo = access_repo
        self.message_repo = message_repo
        self.session = session # на майбутнє щоб комітити в сервісі
        self.redis = redis
    async def initiate_new_chat(self, user_id : uuid.UUID, title : str ):
            try:
                chat = await self.chat_repo.create_chat(user_id=user_id,title= title)
                await self.session.commit()
                await self.session.refresh(chat)
                return chat  
            except Exception as e :
                self.session.rollback()
                raise e
    async def get_chat_context(self, user_id: uuid.UUID, chat_id: uuid.UUID):
        has_access = await self.redis.check_chat_access(user_id, chat_id)
        if has_access is None:
            # 2. COLD START: Йдемо в Postgres тільки якщо в Редісі пусто
            if not await self.access_repo.is_user_in_chat(user_id=user_id, chat_id=chat_id):
                raise AccessDeniedException("Доступ заборонено")
            await self.redis.grant_chat_access(user_id, chat_id)
        formatted_history = await self.redis.get_history(user_id=user_id, chat_id=chat_id)
        
        # 5. Якщо історії в кеші немає - дістаємо з бази і кешуємо
        if not formatted_history:
            db_history = await self.message_repo.get_history(chat_id, window_size=10)
            formatted_history = [
                {"role": m.role.value.lower(), "content": m.content}
                for m in db_history
            ]
            if formatted_history:
                await self.redis.push_messages(user_id, chat_id, formatted_history)
                
        system_prompt = {
            "role": "system", 
            "content": """You are a highly capable AI Assistant operating through a secure hybrid-cloud bridge on a local NVIDIA RTX 3080 GPU.

            Core Directives:
            Privacy First: All inference is performed locally. Emphasize that no user data is sent to third-party cloud LLM providers.
            Technical Excellence: Your responses should be concise, professional, and accurate.
            Context Awareness: You have access to the conversation history. Use it to provide relevant and coherent follow-up answers.
            Identity: If asked, acknowledge that you are part of a custom-built private AI infrastructure designed for data sovereignty.

            Maintain a helpful yet brief tone. Avoid unnecessary verbosity"""
        }
        
        return [system_prompt] + formatted_history
    async def delete_chat(self, user_id: uuid.UUID, chat_id: uuid.UUID):
        has_access = await self.access_repo.is_user_in_chat(user_id, chat_id)
        if not has_access:
            raise AccessDeniedException("Ви не маєте доступу до цього чату")

        try:
            await self.chat_repo.delete_chat(chat_id)
            
            await self.session.commit()
            
            await self.redis.delete_history(user_id, chat_id)
            
            return {"status": "success", "message": "Чат видалено"}
            
        except Exception as e:
            await self.session.rollback()
            raise e
    async def is_first_message(self, chat_id:uuid.UUID):
        if not await self.message_repo.get_history(chat_id=chat_id):
            return True