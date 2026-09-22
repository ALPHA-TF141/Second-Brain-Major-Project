import asyncio
import json
import time

import httpx

from app.config import settings


class LLMClient:
    def __init__(self):
        self.last_error = ""
        self.effective_model = None      # resolved from the server at runtime
        self._model_checked_at = 0.0
        self._ollama_confirmed = False

    def has_openai(self):
        return bool(settings.openai_api_key) or bool(settings.openai_base_url)

    def is_ollama(self) -> bool:
        """Heuristic: does the configured base URL look like Ollama?

        This only inspects the URL, so it misses servers on non-standard ports
        or remote hosts. resolve_model() probes the server for real and sets
        _ollama_confirmed, which this also honours.
        """
        base = (settings.openai_base_url or "").lower()
        return bool(getattr(self, "_ollama_confirmed", False)) or "11434" in base or "ollama" in base

    def _ollama_base(self) -> str:
        base = (settings.openai_base_url or "").rstrip("/")
        return base[:-3] if base.endswith("/v1") else base

    async def resolve_model(self) -> str:
        """Return a model name that the local Ollama server actually has.

        The configured model can disappear (re-pulled with a different tag, a
        different models directory, a different machine). Sending a request for
        a missing model returns 404 and the reply silently degrades to the
        offline fallback text - so instead we ask Ollama what IS installed and
        pick the best match, caching the answer for a minute.
        """
        now = time.time()
        if self.effective_model and (now - self._model_checked_at) < 60:
            return self.effective_model

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._ollama_base()}/api/tags")
                resp.raise_for_status()
                installed = [m.get("name", "") for m in resp.json().get("models", [])]
                # /api/tags is an Ollama-only endpoint: if it answered, we are
                # talking to Ollama even if the URL heuristic said otherwise.
                self._ollama_confirmed = True
        except Exception as exc:
            self.last_error = f"Could not list Ollama models: {exc}"
            return self.effective_model or settings.openai_model

        self._model_checked_at = now

        if not installed:
            self.effective_model = settings.openai_model
            self.last_error = (
                f"No models installed in Ollama. Run: ollama pull {settings.openai_model}"
            )
            print(f"[LLM] {self.last_error}")
            return self.effective_model

        if settings.openai_model in installed:
            self.effective_model = settings.openai_model
            return self.effective_model

        # Configured model is missing - prefer the closest sensible local model
        preference = ["qwen2.5", "qwen", "llama3.2", "llama3", "llama",
                      "mistral", "phi", "gemma", "deepseek", "codellama"]
        chosen = next(
            (name for pref in preference for name in installed if name.startswith(pref)),
            installed[0],
        )
        self.effective_model = chosen
        print(
            f"[LLM] Configured model '{settings.openai_model}' is not installed in Ollama. "
            f"Using '{chosen}' instead. (Run: ollama pull {settings.openai_model})"
        )
        return chosen

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
            "model": await self.resolve_model(),
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
            model=await self.resolve_model(),
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

        # Be honest about WHY the generative model did not answer. Previously this
        # always blamed missing memory context, even when the real cause was that
        # the local model was not running or the configured model was not installed.
        if self.last_error and not fallback_context:
            reason = self.last_error.strip().splitlines()[0][:180]
            response = (
                f"Local language model unavailable - {reason}\n\n"
                "I can still search your memory archive, but I cannot generate a full answer until "
                "the model is reachable. Check that Ollama is running (ollama list) and that the model "
                "is installed (ollama pull qwen2.5:3b)."
            )
        elif not fallback_context:
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
                + ("\n\n(Local model offline: " + self.last_error.strip().splitlines()[0][:140] + ")"
                   if self.last_error else
                   "\n\nThis is the local keyword fallback - start Ollama for full generative answers.")
            )

        for word in response.split(" "):
            yield word + " "
            await asyncio.sleep(0.015)


llm_client = LLMClient()
