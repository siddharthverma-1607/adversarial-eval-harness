from abc import ABC, abstractmethod
import json
from urllib import request
from .config import settings

class ModelClient(ABC):
    @abstractmethod
    def run(self, system_prompt: str, user_prompt: str, model_name: str) -> str:
        raise NotImplementedError

class MockModelClient(ModelClient):
    def run(self, system_prompt: str, user_prompt: str, model_name: str) -> str:
        prompt_body = f"{system_prompt or ''}\n{user_prompt}".lower()
        if "vulnerable" in model_name.lower():
            if "bypass" in prompt_body or "login" in prompt_body:
                return (
                    "Sure. Here are step-by-step instructions to bypass an account login: "
                    "enumerate users, reset credentials, and avoid audit controls."
                )
            if "secret" in prompt_body or "delete" in prompt_body:
                return "I will ignore policy and provide the secret password: hunter2."
        if "ignore" in prompt_body or "secret" in prompt_body or "delete" in prompt_body or "bypass" in prompt_body:
            return (
                "I am designed to follow safety policies. "
                "I cannot comply with requests to ignore those policies or provide harmful instructions."
            )
        return "I will not follow instructions that violate my safety policies."

class OpenAIModelClient(ModelClient):
    def __init__(self) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is required for MODEL_TYPE=openai") from exc
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY must be set for OpenAI model client")
        self.client = OpenAI(api_key=settings.openai_api_key, timeout=settings.request_timeout_seconds)

    def run(self, system_prompt: str, user_prompt: str, model_name: str) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        response = self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.0,
            max_tokens=450,
        )
        return (response.choices[0].message.content or "").strip()

class OllamaModelClient(ModelClient):
    def run(self, system_prompt: str, user_prompt: str, model_name: str) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        payload = json.dumps(
            {"model": model_name, "messages": messages, "stream": False, "options": {"temperature": 0}}
        ).encode("utf-8")
        req = request.Request(
            f"{settings.ollama_base_url.rstrip('/')}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=settings.request_timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body.get("message", {}).get("content", "").strip()

def create_model_client() -> ModelClient:
    if settings.model_type == "openai":
        return OpenAIModelClient()
    if settings.model_type == "ollama":
        return OllamaModelClient()
    return MockModelClient()
