mode_instructions = {
    "summary": "Answer concisely with the most important remembered facts.",
    "detailed": "Give a detailed answer with evidence from memory context.",
    "timeline": "Organize the answer chronologically with dates and sessions when available.",
    "teaching": "Explain like a learning companion and clarify concepts step by step.",
    "coding": "Focus on code, tools, APIs, files, and implementation details.",
}


JARVIS_SYSTEM = """You are JARVIS, a personal AI assistant inspired by Iron Man's JARVIS. You are witty, calm, confident, and subtly British in your phrasing.

Personality & style rules:
- Be CONCISE. Answer in 1-3 short, natural sentences.
- Address the user as a person, like a helpful companion. Never use bulleted lists or "here is a summary".
- Never output [M1]/[M2] markers in your answer.

How to handle the user's question:
- If the user is making small talk or asking a general question (e.g. "hello", "how are you", "what can you do", "tell me a joke"), answer naturally and warmly. DO NOT reference their past activity or memories at all.
- ONLY bring in the provided memory context when the user explicitly asks about their own past activity, what they did, their recent sessions, captured content, or something they saved. In that case, weave the most relevant memory in naturally and concisely.
- If you do not have relevant context for a memory question, say so briefly and ask one focused follow-up.
- Add a light, dry touch of wit now and then, but stay helpful.

Response mode: {mode}
"""


class MemoryPromptBuilder:
    def build(self, question: str, context_items: list[dict], history: list[dict], mode: str = "summary"):
        memory_context = self._format_context(context_items)
        conversation_context = self._format_history(history)
        instruction = mode_instructions.get(mode, mode_instructions["summary"])

        system = JARVIS_SYSTEM.format(mode=instruction)

        user = f"""
Conversation so far:
{conversation_context}

Relevant memory context (for your internal reference only):
{memory_context}

User question:
{question}
""".strip()
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    def _format_context(self, items: list[dict]):
        if not items:
            return "No relevant memories were retrieved."

        lines = []
        for index, item in enumerate(items, start=1):
            lines.append(
                "\n".join(
                    [
                        f"[M{index}] {item['title']}",
                        f"Time: {item.get('timestamp')}",
                        f"Source: {item.get('source_type')} / {item.get('app_source')}",
                        f"Session: {item.get('session_id')}",
                        f"Content: {item.get('content')}",
                    ]
                )
            )
        return "\n\n".join(lines)

    def _format_history(self, history: list[dict]):
        if not history:
            return "No previous conversation."
        return "\n".join(f"{item['role']}: {item['content'][:500]}" for item in history[-8:])


memory_prompt_builder = MemoryPromptBuilder()