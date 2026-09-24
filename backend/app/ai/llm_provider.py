import json
from pathlib import Path
import subprocess
import sys
import threading

from app.config.settings import settings


class AgentBusyError(RuntimeError):
    """Raised when the local investigation model is already generating."""


class AgentUnavailableError(RuntimeError):
    """Raised when the configured local generation model cannot be loaded."""


class AgentTimeoutError(RuntimeError):
    """Raised when local generation exceeds the configured deadline."""


class AgentOutputError(RuntimeError):
    """Raised when generated output is empty, malformed, or not grounded."""


class BaseLLMProvider:
    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict,
        max_tokens: int,
    ) -> dict:
        raise NotImplementedError


class LocalTransformersProvider(BaseLLMProvider):
    """Lazy, CPU-friendly local instruction-model provider."""

    def __init__(self):
        self._lock = threading.Lock()
        self._active = False

    @property
    def name(self) -> str:
        return settings.INVESTIGATION_MODEL_NAME

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict,
        max_tokens: int,
    ) -> dict:
        if not self._lock.acquire(blocking=False):
            raise AgentBusyError("The investigation agent is already busy.")
        try:
            request = json.dumps({
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "max_tokens": max_tokens,
            })
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "app.ai.investigation_worker"],
                    input=request,
                    text=True,
                    capture_output=True,
                    timeout=settings.INVESTIGATION_TIMEOUT_SECONDS,
                    cwd=str(Path(__file__).resolve().parents[2]),
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise AgentTimeoutError(
                    "The local investigation model exceeded its time limit."
                ) from exc

            if result.returncode != 0:
                raise AgentUnavailableError(
                    "The local investigation model worker is unavailable."
                )
            try:
                envelope = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                raise AgentOutputError(
                    "The investigation model worker returned malformed output."
                ) from exc
            if not envelope.get("ok") or not isinstance(envelope.get("text"), str):
                raise AgentOutputError(
                    "The investigation model worker did not return generated text."
                )
            return _parse_json_object(envelope["text"])
        finally:
            self._lock.release()


def _parse_json_object(text: str) -> dict:
    if not text:
        raise AgentOutputError("The investigation model returned an empty response.")
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise AgentOutputError("The investigation model did not return a JSON object.")
    try:
        value = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise AgentOutputError("The investigation model returned malformed JSON.") from exc
    if not isinstance(value, dict):
        raise AgentOutputError("The investigation model response must be a JSON object.")
    return value


_provider = LocalTransformersProvider()


def get_llm_provider() -> BaseLLMProvider:
    return _provider


def set_llm_provider(provider: BaseLLMProvider | None) -> None:
    """Replace the provider for tests; production uses the lazy local provider."""
    global _provider
    _provider = provider or LocalTransformersProvider()
