from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
from src.worker import celery_app
from src.core.dependencies import RagServiceFactory, RagService
from src.api.schemas import TaskData, PromptRequest, UserRequest
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
async def chat_stream(prompt: str, chat_id: UUID, user = Depends(get_current_user), chat_service = Depends(get_chat_service)):

    context = await chat_service.get_chat_context(user.id, chat_id)
    
    context.append({'role': 'user', 'content': prompt})

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

        await chat_service.save_interaction(
            user_id=user.id,
            chat_id=chat_id,
            user_content=prompt,
            assistant_content=full_response,
            metadata=metadata 
        )

    return StreamingResponse(generate(), media_type="text/plain")
@router.post("/chats", response_model=ChatResponse)
async def create_chat(user = Depends(get_current_user), chat_service : ChatService = Depends(get_chat_service)):
    return await chat_service.initiate_new_chat(user.id)
@router.get("/chats{limit}/{offset}", response_model=list[ChatResponse])
async def create_chat(limit : int, offset : int ,user = Depends(get_current_user), chat_service: ChatService = Depends(get_chat_service)):
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