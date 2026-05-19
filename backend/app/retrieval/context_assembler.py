class ContextAssembler:
    def assemble(self, query: str, memories: list, max_items: int = 6):
        selected = memories[:max_items]
        context = []
        for memory in selected:
            context.append(
                {
                    "memory_id": memory.id,
                    "title": memory.title,
                    "content": memory.content[:900],
                    "source_type": memory.source_type,
                    "app_source": memory.app_source,
                    "session_id": memory.session_id,
                    "timestamp": memory.created_at,
                }
            )
        return {"query": query, "items": context}


context_assembler = ContextAssembler()
