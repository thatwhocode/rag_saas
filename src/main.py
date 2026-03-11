from fastapi import APIRouter, FastAPI
from src.api.routes import router
from src.auth.auth import auth_router
from contextlib import asynccontextmanager
from src.api.routes import rag_factory
from shared_packages.core.config import RedisSettings
from src.services.redis import RedisService
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


    