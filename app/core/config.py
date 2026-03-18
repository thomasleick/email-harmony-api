from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "prod"
    GEMINI_API_KEY: str = ""
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra='ignore')

settings = Settings()
