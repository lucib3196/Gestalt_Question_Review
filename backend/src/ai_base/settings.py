import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class AISettings(BaseSettings):
    PROVIDER: str
    MODEL: str

    OPENAI_API_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra="ignore" # Ignore extra env stuff


ai_settings = AISettings(
    PROVIDER=str(os.getenv("AI_PROVIDER", "openai")),
    MODEL=str(os.getenv("MODEL", "gpt-4o")),
    OPENAI_API_KEY=str(os.getenv("OPENAI_API_KEY")),
)
