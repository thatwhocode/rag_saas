from pydantic import BaseModel
import uuid
from typing import Optional
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenUser(BaseModel):
    id: uuid.UUID
    username : Optional[str] = None