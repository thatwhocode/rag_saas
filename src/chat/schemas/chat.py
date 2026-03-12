from shared_packages.schemas.base import CoreModel
import uuid
from datetime import datetime
class ChatResponse(CoreModel):
    id: uuid.UUID
    title: str
    created_at: datetime


class ChatStreamRequest(CoreModel):
    prompt: str
    chat_id: uuid.UUID