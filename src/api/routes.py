from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
from src.worker import celery_app
from src.core.dependencies import RagServiceFactory, RagService
from src.api.schemas import TaskData, PromptRequest, UserRequest
from src.chat.schemas.chat import ChatStreamRequest
import os
import shutil
from shared_packages.core.config import LLMSettings
from celery.result import AsyncResult
from src.worker import process_document_task
from src.api.deps import get_current_user, get_chat_service, ChatService
from src.db.user import User
from ollama import AsyncClient
from uuid import UUID
from src.chat.schemas.chat import ChatResponse
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
async def chat_stream(chat_request: ChatStreamRequest, user = Depends(get_current_user), chat_service = Depends(get_chat_service)):
    # Отримуємо історію чату
    db_context = await chat_service.get_chat_context(user.id, chat_request.chat_id)
    
    formatted_context = []
    for msg in db_context:
        # Безпечно дістаємо роль та контент
        # Працює і для об'єктів SQLAlchemy, і для звичайних словників
        if isinstance(msg, dict):
            role = msg.get('role')
            content = msg.get('content')
        else:
            role = getattr(msg, 'role', 'assistant')
            content = getattr(msg, 'content', '')

        # Додаткова перевірка, якщо роль — це Enum (SQLAlchemy часто так робить)
        role_str = role.value if hasattr(role, 'value') else str(role)
        
        formatted_context.append({"role": role_str, "content": content})
    
    # Додаємо поточне запитання юзера
    formatted_context.append({'role': 'user', 'content': chat_request.prompt})

    async def generate():
        # Створюємо клієнт тут, щоб уникнути конфліктів loop
        client = AsyncClient(host=ollama.OLLAMA_URL)
        full_response = ""
        
        try:
            print(f"DEBUG: Connecting to Ollama at {ollama.OLLAMA_URL}")
            response = await client.chat(
                model=ollama.CHAT_MODEL,
                messages=formatted_context,
                stream=True
            )
            
            async for part in response:
                content = part['message']['content']
                full_response += content
                yield content
            
            # Зберігаємо тільки якщо стрім дочитали до кінця
            await chat_service.save_interaction(user.id, chat_request.chat_id, chat_request.prompt, full_response, {})
            
        except Exception as e:
            print(f"🚨 OLLAMA ERROR: {str(e)}")
            yield f"\n[Backend Error]: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")
@router.post("/chats", response_model=ChatResponse)
async def create_chat(user = Depends(get_current_user), chat_service : ChatService = Depends(get_chat_service)):
    return await chat_service.initiate_new_chat(user.id)
@router.get("/chats/{limit}/{offset}", response_model=list[ChatResponse])
async def load_chat(limit : int =10, offset : int =0 ,user = Depends(get_current_user), chat_service: ChatService = Depends(get_chat_service)):
    return await chat_service.chat_repo.get_user_chats(user.id, limit, offset)
@router.delete("/chat{chat_id}", response_model=list[ChatResponse])
async def create_chat(chat_id : UUID ,user = Depends(get_current_user), chat_service: ChatService = Depends(get_chat_service)):
    return await chat_service.chat_repo.delete_chat(chat_id)
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