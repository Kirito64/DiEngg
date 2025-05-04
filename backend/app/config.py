from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Diengg"
    
    # Environment Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Milvus Configuration
    MILVUS_HOST: str
    MILVUS_PORT: int
    MILVUS_USER: str
    MILVUS_PASSWORD: str
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings() 