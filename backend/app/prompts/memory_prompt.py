mode_instructions = {
    "summary": "Answer concisely with the most important remembered facts.",
    "detailed": "Give a detailed answer with evidence from memory context.",
    "timeline": "Organize the answer chronologically with dates and sessions when available.",
    "teaching": "Explain like a learning companion and clarify concepts step by step.",
    "coding": "Focus on code, tools, APIs, files, and implementation details.",
}


class MemoryPromptBuilder:
    def build(self, question: str, context_items: list[dict], history: list[dict], mode: str = "summary"):
        memory_context = self._format_context(context_items)
        conversation_context = self._format_history(history)
        instruction = mode_instructions.get(mode, mode_instructions["summary"])

        system = (
            "You are Second Brain, a personal cognitive memory assistant. "
            "Use only the provided memory context when answering about the user's past activity. "
            "If context is missing, say what is missing and suggest how to capture or index it. "
            "Cite memories using [M1], [M2], etc when useful. "
            f"Response mode: {instruction}"
        )

        user = f"""
Conversation so far:
{conversation_context}

Relevant memory context:
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
