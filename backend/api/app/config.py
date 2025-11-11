from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置"""

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/wordloom_v3"

    # Debug
    DEBUG: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()