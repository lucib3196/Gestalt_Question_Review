from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field
from typing import Optional
from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel, ValidationError


# Points to the root directory C://User/GestaltQuestions adjust as needed
ROOT_PATH = Path(__file__).parents[3]


class AIModel(BaseModel):
    name: Optional[str] = None  # A name such as (fast, long context etc)
    provider: str = Field(..., description="e.g. Openai, gemini, claude etc")
    model: str = Field(..., description="e.g. gpt-4o-mini, claude 3 opus")
    api_key: Optional[str] = Field(None, description="API Key for this provider")
    base_url: Optional[str] = None  # optional custom endpoint


class AICoreSettings(BaseSettings):
    default_api_key: Optional[str] = Field(
        None, description="Fallback key if model missing"
    )
    fast_model: Optional[AIModel] = None
    base_model: AIModel
    long_context_model: Optional[AIModel] = None

    langsmith_tracing: bool = True
    langsmith_project: Optional[str] = "ai_ucr"
    
    embedding_model: str

    def get_api_key(self, model_name: str) -> str | None:
        model = getattr(self, model_name)
        return model.api_key or self.default_api_key

    model_config = SettingsConfigDict(
        env_prefix="AI_", env_file=ROOT_PATH / "ai.env", env_nested_delimiter="__"
    )


@lru_cache
def get_settings() -> AICoreSettings:
    return AICoreSettings()  # type: ignore


if __name__ == "__main__":
    try:
        print(get_settings().model_dump())
    except ValidationError as e:
        print(e)
