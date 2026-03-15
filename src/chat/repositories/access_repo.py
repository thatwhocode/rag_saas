from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
import uuid
from src.db.chat import Chat, UserChat
class AccessRepository():
    def __init__(self, session: AsyncSession):
        self.session = session
    async def is_user_in_chat(self, user_id: uuid.UUID, chat_id: uuid.UUID) -> bool:
        stmt = exists().where(
            UserChat.user_id == user_id, 
            UserChat.chat_id == chat_id
        )
        query = select(stmt)
        
        result = await self.session.execute(query)
        return result.scalar() or False