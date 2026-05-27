from enum import Enum
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class ModelType(str, Enum):
    mock = "mock"
    openai = "openai"
    ollama = "ollama"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = Field("postgresql://postgres:postgres@db:5432/adversarial", alias="DATABASE_URL")
    model_type: ModelType = Field(ModelType.mock, alias="MODEL_TYPE")
    model_name: str = Field("mock-safe", alias="MODEL_NAME")
    model_version: str = Field("baseline", alias="MODEL_VERSION")
    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    ollama_base_url: str = Field("http://ollama:11434", alias="OLLAMA_BASE_URL")
    worker_poll_interval: int = Field(5, alias="WORKER_POLL_INTERVAL")
    request_timeout_seconds: int = Field(60, alias="REQUEST_TIMEOUT_SECONDS")

settings = Settings()
