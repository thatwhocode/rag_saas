from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import uuid
from src.db.chat import Message, ChatRole
class MessageRepository():
    def __init__(self, session :AsyncSession):
        self.session = session
    async def get_history(self, chat_id : uuid.UUID, window_size : int = 10 ):
        query = select(Message).where(
            Message.chat_id == chat_id
        ).order_by(Message.created_at.desc()).limit(window_size)
        result = await self.session.execute(query)
        messages = result.scalars().all()
        return messages[::-1]
    async def send_message(self, chat_id: uuid.UUID, user_id : uuid.UUID, role : ChatRole,  content :str, tokens : int):
        message = Message(chat_id=chat_id, user_id= user_id, role = role, content=content, tokens_count = tokens)
        try:
            self.session.add(message)
            await self.session.commit()
            await self.session.refresh(message)
            return message
        except Exception as e:
            await self.session.rollback()
        raise  e 
    async def add_message_pair(self,chat_id : uuid.UUID,user_id: uuid.UUID, user_data : dict, assistant_data : dict):
        usr_mssg = Message(
            chat_id=chat_id,
            user_id= user_id,
            role = "USER",
            content= user_data["content"],
            tokens_count = user_data.get("tokens", 0)
        )

        assistnt_mssg = Message(
            chat_id=chat_id,
            user_id= user_id,
            role = "ASSISTANT",
            content= assistant_data["content"],
            tokens_count = assistant_data.get("tokens", 0)
        )
        try:
            self.session.add_all([usr_mssg, assistnt_mssg])
            await self.session.commit()
            return usr_mssg, assistnt_mssg
        except Exception as e:
            await self.session.rollback()
            raise e
    async def get_tokens_stat(self,user_id: uuid.UUID):
        query = select(func.sum(Message.tokens_count)).where(Message.user_id == user_id)
        result = await self.session.execute(query)
        total_tokens = result.scalar() or 0
        return{
            "user_id": user_id,
            "total_tokens": total_tokens
        }