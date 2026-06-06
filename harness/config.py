import os
from enum import Enum
from pydantic import BaseSettings, Field

class ModelType(str, Enum):
    mock = "mock"
    openai = "openai"

class Settings(BaseSettings):
    database_url: str = Field("postgresql://postgres:postgres@db:5432/adversarial", env="DATABASE_URL")
    model_type: ModelType = Field(ModelType.mock, env="MODEL_TYPE")
    model_name: str = Field("gpt-4.1", env="MODEL_NAME")
    model_version: str = Field("latest", env="MODEL_VERSION")
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    worker_poll_interval: int = Field(5, env="WORKER_POLL_INTERVAL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
