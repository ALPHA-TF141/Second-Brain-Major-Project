import asyncio
import json

import httpx

from app.config import settings


class LLMClient:
    def __init__(self):
        self.last_error = ""

    def has_openai(self):
        return bool(settings.openai_api_key) or bool(settings.openai_base_url)

    async def stream(self, messages: list[dict], fallback_context: list[dict]):
        if self.has_openai():
            # If pointing to local Ollama, prefer Ollama's native /api/chat which is 100% reliable
            is_ollama = "11434" in settings.openai_base_url or "ollama" in settings.openai_base_url.lower()

            if is_ollama:
                try:
                    async for token in self._stream_ollama(messages):
                        yield token
                    return
                except Exception as exc:
                    self.last_error = str(exc)
                    print(f"[LLM] Ollama native stream failed: {exc}, attempting OpenAI endpoint...")

            # Otherwise or fallback: try OpenAI compatibility endpoint
            try:
                async for token in self._stream_openai(messages):
                    yield token
                return
            except Exception as exc:
                self.last_error = str(exc)
                print(f"[LLM] OpenAI stream failed: {exc}")

            # If both fail, try Ollama native as secondary fallback before local rules
            if not is_ollama:
                try:
                    async for token in self._stream_ollama(messages):
                        yield token
                    return
                except Exception:
                    pass

        async for token in self._stream_local_fallback(messages, fallback_context):
            yield token

    async def _stream_ollama(self, messages: list[dict]):
        """Native Ollama streaming API (/api/chat) which works directly with all Ollama models."""
        base = settings.openai_base_url.rstrip("/")
        if base.endswith("/v1"):
            base = base[:-3]
        url = f"{base}/api/chat"

        payload = {
            "model": settings.openai_model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.2},
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream("POST", url, json=payload) as resp:
                if resp.status_code != 200:
                    err_body = await resp.aread()
                    raise RuntimeError(f"Ollama returned {resp.status_code}: {err_body.decode('utf-8', errors='ignore')}")

                async for line in resp.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token

    async def _stream_openai(self, messages: list[dict]):
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key or "ollama", base_url=settings.openai_base_url)
        stream = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.2,
            stream=True,
        )
        async for event in stream:
            token = event.choices[0].delta.content or ""
            if token:
                yield token

    async def _stream_local_fallback(self, messages: list[dict], fallback_context: list[dict]):
        question = messages[-1]["content"].split("User question:")[-1].strip()
        if not fallback_context:
            response = (
                "I do not have enough indexed memory context to answer that yet. "
                "Capture activity, process OCR, rebuild the memory archive, and index semantic memories first."
            )
        else:
            bullets = []
            for index, item in enumerate(fallback_context[:5], start=1):
                bullets.append(f"[M{index}] {item['title']}: {item['content'][:260]}")
            response = (
                f"Based on your saved memories, here is the best local answer to: {question}\n\n"
                + "\n\n".join(bullets)
                + "\n\nThis is the local fallback response. Add OPENAI_API_KEY for richer generative answers."
            )

        for word in response.split(" "):
            yield word + " "
            await asyncio.sleep(0.015)


llm_client = LLMClient()
