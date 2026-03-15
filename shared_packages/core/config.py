import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field, model_validator

class SharedBaseSettings(BaseSettings):
    """
    Базовий клас. Містить логіку читання секретів та загальні налаштування.
    """
    APP_NAME: str = "Microservice"
    MODE: str = "DEV"
    

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    

    SECRET_KEY_FILE: Optional[str] = None
    SECRET_KEY: str = "change_me_in_prod"
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore", 
        env_file_encoding="utf-8"
    )

    def _get_secret_value(self, file_path: Optional[str], env_value: Optional[str], var_name: str) -> str:
        """Розумна читалка: пріоритет файлу -> змінна -> помилка"""
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    return f.read().strip()
            except Exception as e:
                print(f"⚠️ Warning: Could not read secret file {file_path}: {e}")

        if env_value and env_value != "localhost" and env_value != "change_me_in_prod":
            return env_value
        
        if self.MODE == "DEV" and env_value:
             return env_value

        return env_value or "missing_secret"

    @model_validator(mode='after')
    def set_security_secrets(self) -> 'SharedBaseSettings':
        self.SECRET_KEY = self._get_secret_value(
            self.SECRET_KEY_FILE, 
            self.SECRET_KEY, 
            "SECRET_KEY"
        )
        return self


class PostgresSettings(SharedBaseSettings):
    """
    Налаштування тільки для баз даних
    """
    POSTGRES_HOST_FILE: Optional[str] = None
    POSTGRES_HOST: str = "llm_chat_db"
    
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"
    POSTGRES_DB_FILE : Optional[str] = None

    POSTGRES_USER_FILE: Optional[str] = None
    POSTGRES_USER: Optional[str] = None

    POSTGRES_PASSWORD_FILE: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        host = self._get_secret_value(self.POSTGRES_HOST_FILE, self.POSTGRES_HOST, "host")
        user = self._get_secret_value(self.POSTGRES_USER_FILE, self.POSTGRES_USER, "user")
        password = self._get_secret_value(self.POSTGRES_PASSWORD_FILE, self.POSTGRES_PASSWORD, "password")
        postgres_db = self._get_secret_value(self.POSTGRES_DB_FILE, self.POSTGRES_DB,"db_name" )
        
        return f"postgresql+asyncpg://{user}:{password}@{host}:{self.POSTGRES_PORT}/{postgres_db}"


class RedisSettings(SharedBaseSettings):
    """ Redis
    """
    REDIS_HOST: str = "llm_redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD_FILE: Optional[str] = None
    REDIS_PASSWORD : str =  "my_strong_redis_password"
    @computed_field
    @property
    def REDIS_URL(self) -> str:
        password = self._get_secret_value(self.REDIS_PASSWORD_FILE, self.REDIS_PASSWORD, "password")
        return f"redis://:{password}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
class QdrantSettings(SharedBaseSettings):
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "user_knowledge_base"

    @computed_field
    @property
    def QDRANT_URL(self) -> str:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"

class LLMSettings(SharedBaseSettings):
    """ Налаштування для локальних/хмарних моделей """
    OLLAMA_HOST: str = "ollama"
    OLLAMA_PORT: int = 11434
    EMBED_MODEL: str = "nomic-embed-text"
    CHAT_MODEL: str = "llama3"

    @computed_field
    @property
    def OLLAMA_URL(self) -> str:
        return f"http://{self.OLLAMA_HOST}:{self.OLLAMA_PORT}"