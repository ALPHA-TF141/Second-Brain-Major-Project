import re


class SemanticChunker:
    def chunk(self, clean_text: str):
        blocks = [block.strip() for block in re.split(r"\n\s*\n", clean_text) if block.strip()]
        chunks = []

        for block in blocks:
            chunk_type = self._source_type(block)
            topic = self._topic_label(block, chunk_type)
            chunks.append({"content": block, "source_type": chunk_type, "topic_label": topic})

        return chunks

    def _source_type(self, text: str):
        code_markers = ["def ", "class ", "import ", "const ", "function ", "{", "};", "return "]
        youtube_markers = ["subscribe", "views", "lecture", "youtube"]
        pdf_markers = ["page ", "chapter", "figure", "references"]

        lowered = text.lower()
        if any(marker in text for marker in code_markers):
            return "code"
        if any(marker in lowered for marker in youtube_markers):
            return "youtube"
        if any(marker in lowered for marker in pdf_markers):
            return "document"
        if len(text.split()) > 80:
            return "article"
        return "screen"

    def _topic_label(self, text: str, source_type: str):
        first_line = text.splitlines()[0].strip()
        if 6 <= len(first_line) <= 80:
            return first_line[:80]
        if source_type == "code":
            return "Code Practice"
        if source_type == "youtube":
            return "Video Learning"
        if source_type == "document":
            return "Document Reading"
        return "Screen Notes"
