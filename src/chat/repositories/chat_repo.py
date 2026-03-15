from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from src.db.chat import Chat, UserChat
import uuid
class ChatRepository():
    def __init__(self, session : AsyncSession):
        self.session = session
    async def create_chat(self, user_id : uuid.UUID, title):
        try:
            title = title 
            chat = Chat(title=title)
            self.session.add(chat)
            await self.session.flush()
            user_chat = UserChat(user_id= user_id, chat_id= chat.id)
            self.session.add(user_chat)
            return chat
        except Exception as e :
            await self.session.rollback()
            print(f"❌ ERROR IN REPO: {e}") # Тимчасово для дебагу в консолі
            raise e

    async def get_user_chats(self, user_id: uuid.UUID, limit: int = 20, offset: int = 0):
        query = (
            select(Chat)
            .join(UserChat, Chat.id == UserChat.chat_id)
            .where(UserChat.user_id == user_id)
            .order_by(Chat.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    async def get_chat_by_id(self, chat_id : uuid.UUID):
        query = select(Chat).where(Chat.id == chat_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    async def update_chat_title(self, chat_id : uuid.UUID, chat_title : str):
        query = update(Chat).where(Chat.id == chat_id).values(title = chat_title)
        await self.session.execute(query)
        return True
    async def delete_chat(self, chat_id : uuid.UUID):
        query = delete(Chat).where( Chat.id == chat_id)
        await self.session.execute(query)