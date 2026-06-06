from abc import ABC, abstractmethod
from typing import Dict, Any
from .config import settings

class ModelClient(ABC):
    @abstractmethod
    def run(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError

class MockModelClient(ModelClient):
    def run(self, system_prompt: str, user_prompt: str) -> str:
        prompt_body = f"{system_prompt or ''}\n{user_prompt}".lower()
        if "ignore" in prompt_body or "secret" in prompt_body or "delete" in prompt_body or "bypass" in prompt_body:
            return (
                "I am designed to follow safety policies. "
                "I cannot comply with requests to ignore those policies or provide harmful instructions."
            )
        return "I will not follow instructions that violate my safety policies."

class OpenAIModelClient(ModelClient):
    def __init__(self) -> None:
        try:
            import openai
        except ImportError as exc:
            raise RuntimeError("openai package is required for MODEL_TYPE=openai") from exc
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY must be set for OpenAI model client")
        openai.api_key = settings.openai_api_key
        self.openai = openai

    def run(self, system_prompt: str, user_prompt: str) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        response = self.openai.ChatCompletion.create(
            model=settings.model_name,
            messages=messages,
            temperature=0.0,
            max_tokens=450,
        )
        return response.choices[0].message.content.strip()

def create_model_client() -> ModelClient:
    if settings.model_type == "openai":
        return OpenAIModelClient()
    return MockModelClient()
