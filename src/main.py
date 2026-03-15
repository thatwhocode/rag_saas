from fastapi import APIRouter, FastAPI, status, Request
from fastapi.responses import JSONResponse
from src.api.routes import router
from src.auth.auth import auth_router
from contextlib import asynccontextmanager
from src.api.routes import rag_factory
from shared_packages.core.config import RedisSettings
from src.services.redis import RedisService
from src.exceptions import UsernameAlreadyInUse, InvalidCredentialsError, UserAlreadyExistsError
redis_settings= RedisSettings()
@asynccontextmanager
async def lifespan(app: FastAPI):

    service = rag_factory()
    await service.vector_store.ensure_collection_exists()
    redis = RedisService(redis_settings.REDIS_URL)
    app.state.redis = redis
    yield
    await app.state.redis.close()

api_version_prefix = "v1"
app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix=f"/{api_version_prefix}/auth", tags=["Auth"])
app.include_router(router, prefix="/LLM", tags=["LLM"])

@app.exception_handler(UsernameAlreadyInUse)
async def username_already_in_use(request: Request, exc: UsernameAlreadyInUse):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail":str(exc)}
    )


@app.exception_handler(UserAlreadyExistsError)
async def user_exists_exception_handler(request: Request, exc: UserAlreadyExistsError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message},
    )

@app.exception_handler(InvalidCredentialsError)
async def auth_exception_handler(request: Request, exc: InvalidCredentialsError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.message},
        headers={"WWW-Authenticate": "Bearer"},
    )
    