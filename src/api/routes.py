from fastapi import APIRouter, UploadFile, File, Depends, status, HTTPException
from fastapi.responses import StreamingResponse
from src.worker import celery_app
from src.db.database import AsyncSessionLocal
from src.core.dependencies import RagServiceFactory, RagService
from src.api.schemas import TaskData, PromptRequest, UserRequest
import os
import shutil
from shared_packages.core.config import LLMSettings
from celery.result import AsyncResult
from src.worker import process_document_task
from src.api.deps import get_current_user, get_chat_service, ChatService, get_redis_service
from src.db.user import User
from ollama import AsyncClient
from uuid import UUID
from src.chat.schemas.chat import ChatResponse, ChatUpdateTitle
from src.chat.repositories.access_repo import AccessRepository
from src.chat.repositories.chat_repo import ChatRepository
from src.chat.repositories.message_repo import MessageRepository
from src.services.redis import RedisService
from shared_packages.core.config import RedisSettings

redis_settings = RedisSettings()
ollama = LLMSettings()

rag_factory = RagServiceFactory(
    qdrant_url="http://qdrant:6333", 
    ollama_host="http://ollama:11434",
    embed_model="nomic-embed-text",
    chat_model="llama3"
)
router = APIRouter()
UPLOAD_PATH : str  = "app/files"
router = APIRouter()

@router.post("/chat/stream")
async def chat_stream(prompt: str, chat_id: UUID, user = Depends(get_current_user), chat_service: ChatService = Depends(get_chat_service)):
    current_chat = await chat_service.chat_repo.get_chat_by_id(chat_id)
    if not current_chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Chat with id {chat_id} not found"
        )
    context = await chat_service.get_chat_context(user.id, chat_id)

    context.append({'role': 'user', 'content': prompt})

    if await chat_service.is_first_message(chat_id) == True and current_chat.title == "New Chat" :
        from src.worker import rename_chat_automatically_task
        rename_chat_automatically_task.delay(str(chat_id), prompt)
    async def generate():
        client = AsyncClient(host=f"{ollama.OLLAMA_URL}")
        full_response = ""
        metadata = {"prompt_eval_count": 0, "eval_count": 0}
        async for part in await client.chat(
            model=ollama.CHAT_MODEL,
            messages=context, 
            stream=True
        ):
            content = part['message']['content']
            full_response += content
            yield content 
            if part.get("done"):
                metadata["prompt_eval_count"] = part.get("prompt_eval_count", 0)
                metadata["eval_count"] = part.get("eval_count", 0)

        async with AsyncSessionLocal() as new_session:
            new_chat_service = ChatService(
                session=new_session,
                chat_repo=ChatRepository(new_session),
                message_repo=MessageRepository(new_session),
                access_repo=AccessRepository(new_session),
                redis= RedisService(redis_settings.REDIS_URL)
            )
            
            await new_chat_service.save_interaction(
                user_id=user.id,
                chat_id=chat_id,
                user_content=prompt,
                assistant_content=full_response,
                metadata=metadata 
            )

    return StreamingResponse(generate(), media_type="text/plain")
@router.post("/chats", response_model=ChatResponse)
async def create_chat(user = Depends(get_current_user), chat_service : ChatService = Depends(get_chat_service)):
    return await chat_service.initiate_new_chat(user.id, title="New Chat")
@router.get("/chats/{limit}/{offset}", response_model=list[ChatResponse])
async def create_chat(limit : int, offset : int ,user = Depends(get_current_user), chat_service: ChatService = Depends(get_chat_service)):
    return await chat_service.chat_repo.get_user_chats(user.id, limit, offset)
@router.delete("/chat/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def create_chat(chat_id : UUID ,user = Depends(get_current_user), chat_service: ChatService = Depends(get_chat_service)):
    return await chat_service.delete_chat(user.id, chat_id)
@router.get("/status/{task_id}")
async def task_status_getter(task_id : str):
    result = AsyncResult(task_id, app=celery_app)
    return {
    "status": result.status, 
    "result": result.result if result.status == "SUCCESS" else None
}
@router.post("/file")
def upload_file(file : UploadFile=File(...), user : User = Depends(get_current_user)):
    
    os.makedirs(UPLOAD_PATH, exist_ok = True)
    file_path  = os.path.join(UPLOAD_PATH, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    

    task = process_document_task.delay(file_path, str(user.id))

    return{
        "file": file.filename,
        "task_id": task.id,
        "message": "File recieved and sent to backgrouund processing"
    }
@router.post("/rag_chat")
async def chat_with_rag(data: UserRequest,  user : User = Depends(get_current_user), service: RagService = Depends(rag_factory)):
    answer = await service.chat_request(question=data.query, user_id=user.id, system_prompt=data.system_prompt)
    return {"answer": answer}
@router.patch("chats/{chat_id}")
async def rename_chat(chat_id : UUID, title : ChatUpdateTitle, chat_service : ChatService = Depends(get_chat_service)):
    return await chat_service.rename_chat(chat_id, title.new_title)
@router.get("/chat/{chat_id}/history_test")
async def get_history_stress_test(
    chat_id: UUID, 
    user = Depends(get_current_user), 
    chat_service: ChatService = Depends(get_chat_service)
):

    cached_history = await chat_service.redis.get_history(user.id, chat_id)
    
    return {"messages_count": len(cached_history) if cached_history else 0}
from fastapi import APIRouter, Depends

