import asyncio
import logging
from collections.abc import Callable
from typing import TypeVar

from zhipuai import ZhipuAI

from ..config.settings import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class GLMClient:
    """Thin async wrapper around the Zhipu AI (GLM) SDK.

    The SDK is synchronous, so calls are offloaded to a worker thread. Retries
    are deliberately simple (fixed attempt count, short backoff) — the
    experiment's unit of work is one item generation, not a high-throughput
    request path, and the quasi-experimental design (Secao 3.7.2 do TCC)
    requires deterministic parameters (temperature, model, max_tokens) to be
    identical across retries.
    """

    def __init__(self) -> None:
        self._client = ZhipuAI(api_key=settings.GLM_API_KEY)

    async def _with_retries(self, func: Callable[[], T]) -> T:
        last_error: Exception | None = None
        for attempt in range(1, settings.GLM_MAX_RETRIES + 1):
            try:
                return await asyncio.wait_for(asyncio.to_thread(func), timeout=settings.GLM_TIMEOUT_SECONDS)
            except Exception as exc:  # noqa: BLE001 — surfaced to the caller after retries are exhausted
                last_error = exc
                logger.warning("GLM call failed (attempt %d/%d): %s", attempt, settings.GLM_MAX_RETRIES, exc)
                if attempt < settings.GLM_MAX_RETRIES:
                    await asyncio.sleep(1.0)
        assert last_error is not None
        raise last_error

    async def generate(self, prompt: str) -> str:
        """Generate an item (or any completion) with the generation model."""

        def _call() -> str:
            response = self._client.chat.completions.create(
                model=settings.GLM_GENERATION_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.GLM_TEMPERATURE,
                max_tokens=settings.GLM_MAX_TOKENS,
            )
            return str(response.choices[0].message.content)

        return await self._with_retries(_call)

    async def judge(self, prompt: str) -> str:
        """Run the LLM-as-Judge evaluation (Camada A, Secao 3.9.2 do TCC)."""

        def _call() -> str:
            response = self._client.chat.completions.create(
                model=settings.GLM_JUDGE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.GLM_TEMPERATURE,
                max_tokens=settings.GLM_MAX_TOKENS,
            )
            return str(response.choices[0].message.content)

        return await self._with_retries(_call)

    async def get_embedding(self, text: str) -> list[float]:
        """Get a semantic embedding for similarity scoring (Camada B, Secao 3.9.1 do TCC)."""

        def _call() -> list[float]:
            response = self._client.embeddings.create(model=settings.GLM_EMBEDDING_MODEL, input=text)
            return [float(x) for x in response.data[0].embedding]

        return await self._with_retries(_call)


_glm_client: GLMClient | None = None


def get_glm_client() -> GLMClient:
    """FastAPI-dependency-friendly accessor for the process-wide GLM client."""
    global _glm_client
    if _glm_client is None:
        _glm_client = GLMClient()
    return _glm_client
