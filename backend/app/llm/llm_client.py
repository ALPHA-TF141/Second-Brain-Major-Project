import asyncio

from app.config import settings


class LLMClient:
    def __init__(self):
        self.last_error = ""

    def has_openai(self):
        return bool(settings.openai_api_key)

    async def stream(self, messages: list[dict], fallback_context: list[dict]):
        if self.has_openai():
            async for token in self._stream_openai(messages):
                yield token
            return

        async for token in self._stream_local_fallback(messages, fallback_context):
            yield token

    async def _stream_openai(self, messages: list[dict]):
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.openai_api_key)
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
        except Exception as exc:
            self.last_error = str(exc)
            yield f"I could not reach the configured LLM, so I cannot generate a full answer. Error: {exc}"

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
