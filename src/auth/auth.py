from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.auth.schemas.user import UserCreate, UserLoginEmail, UserRead, UserLoginUsername, UserUpdate
from src.auth.schemas.token import Token
from src.api.deps import get_current_user, get_auth_service, get_redis_service, get_validated_payload
from src.auth.auth_service import AuthService
from src.services.redis import RedisService
from src.db.user import User
from datetime import timezone, datetime
auth_router = APIRouter()

@auth_router.post("/register", response_model=UserRead)
async def register(
    user_data: UserCreate, 
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.register_user(user_data=user_data)

@auth_router.post("/login_via_email", response_model=Token)
async def login_with_email(
    user_data: UserLoginEmail, 
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.login_with_email(user_data=user_data)

@auth_router.post("/login_via_username", response_model=Token)
async def login_with_username(
    user_data: UserLoginUsername, 
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.login_with_username(user_data=user_data)

@auth_router.post("/token", response_model=Token)
async def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    if "@" in form_data.username:
        login_data = UserLoginEmail(email=form_data.username, password=form_data.password)
        return await auth_service.login_with_email(login_data)
    else:
        login_data = UserLoginUsername(username=form_data.username, password=form_data.password)
        return await auth_service.login_with_username(login_data)

@auth_router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@auth_router.patch("/me/update", response_model=UserRead)
async def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user), 
    auth_service: AuthService = Depends(get_auth_service)
):

    return await auth_service.update_profile(current_user.id, update_data)

@auth_router.post("/logout")
async def logout(
    payload: dict = Depends(get_validated_payload),
    redis: RedisService = Depends(get_redis_service)
):
    jti = payload.get("jti")
    exp = payload.get("exp") 

    now = int(datetime.now(timezone.utc).timestamp())
    ttl = exp - now

    if ttl > 0:
        await redis.add_to_blacklist(jti, ttl)

    return {"message": "Successfully logged out. See you space cowboy!"}