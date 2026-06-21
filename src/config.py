from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from langchain_qwq import ChatQwen

class Settings(BaseSettings):
    dashscope_api_key: str = ""
    model_name: str = "qwen3.5-flash"
    temperature: float = 0.0
    database_url: str 
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

@lru_cache()
def get_llm():
    """Dependency injection factory for the LLM."""
    if not settings.dashscope_api_key:
        raise ValueError("DASHSCOPE_API_KEY environment variable is not set!")
    
    return ChatQwen(
        model=settings.model_name,
        api_key=settings.dashscope_api_key,
        temperature=settings.temperature,
        enable_thinking=False,
    )