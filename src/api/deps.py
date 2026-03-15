from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_db
from src.db.user import User
from src.auth.user_repo import UserRepository
from src.auth.auth_service import AuthService
from src.services.redis import RedisService
from shared_packages.core.security import decode_access_token
from src.chat.repositories.chat_repo import ChatRepository
from src.chat.repositories.message_repo import MessageRepository
from src.chat.repositories.access_repo import AccessRepository
from src.chat.services.chat_service import ChatService
from shared_packages.core.config import RedisSettings
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/token")

redis_settings = RedisSettings()
def get_redis_service(request: Request) -> RedisService:
    return request.app.state.redis

def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_auth_service(user_repo: UserRepository = Depends(get_user_repo)) -> AuthService:
    return AuthService(user_repo.session,user_repo)

def get_chat_service(
    db: AsyncSession = Depends(get_db)):
    return ChatService(db, chat_repo = ChatRepository(db), access_repo = AccessRepository(db), message_repo= MessageRepository(db), redis= RedisService(redis_settings.REDIS_URL))

async def get_validated_payload(
    token: str = Depends(oauth2_scheme),
    redis: RedisService = Depends(get_redis_service)
) -> dict:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="Token missing JTI")

    if await redis.is_in_blacklist(jti):
        raise HTTPException(status_code=401, detail="Token revoked")

    return payload


async def get_current_user(
    payload: dict = Depends(get_validated_payload),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Дістає юзера з бази на основі вже ПЕРЕВІРЕНОГО токена"""
    user_id = payload.get("sub") 
    user = await auth_service.user_repo.find_user_by_id(user_id) 
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    return user