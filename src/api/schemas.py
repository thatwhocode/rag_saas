from pydantic import BaseModel, Field
from typing import Optional
class PromptRequest(BaseModel):
    prompt : str

class TaskData(BaseModel):
    task_id : str
class UserRequest(BaseModel):
    query: str
    system_prompt:  Optional[str] =Field(default="You are a helpful AI assistant. Answer the user's question based strictly on the provided context")