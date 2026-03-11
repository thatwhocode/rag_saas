import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Integer, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base
print(f"--- LOADING CHAT MODELS FROM {__name__} ---")
class ChatRole(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class UserChat(Base):
    __tablename__= "user_chat"
    user_id:  Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id",  ondelete="CASCADE"), primary_key=True)
    chat_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("chat.id",  ondelete="CASCADE"), primary_key=True)
    joined_at : Mapped[datetime] = mapped_column(server_default=func.now())

class Chat(Base):
    __tablename__ = "chat"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at : Mapped[datetime] = mapped_column(server_default=func.now())
    
    messages : Mapped[list["Message"]] = relationship(back_populates="chat", cascade="all, delete-orphan", passive_deletes=True)

class Message(Base):
    __tablename__ = "message"
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        default=uuid.uuid4
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index= True
    )
    role : Mapped[ChatRole] = mapped_column(Enum(ChatRole), default=ChatRole.USER)
    tokens_count : Mapped[int] = mapped_column(Integer, default=0, nullable=False) 
    content: Mapped[str] = mapped_column(Text,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    chat : Mapped["Chat"] =relationship(back_populates="messages")