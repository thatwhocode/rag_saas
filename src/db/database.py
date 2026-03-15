from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from shared_packages.core.config import PostgresSettings


class AuthConfig(PostgresSettings):
    APP_NAME: str = "RAG SaaS Ai"

settings = AuthConfig()

engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI,
                              echo=True,
                              pool_size=100, 
                              max_overflow=50)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit= False,
    
)
class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try: 
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()