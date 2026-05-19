import re


noise_words = {
    "start",
    "search",
    "wifi",
    "battery",
    "type here to search",
    "minimize",
    "maximize",
    "close",
}


class TextCleaner:
    def clean(self, raw_text: str):
        lines = []
        seen = set()

        for line in raw_text.splitlines():
            line = self._normalize(line)
            if not self._is_useful(line):
                continue
            key = line.lower()
            if key in seen:
                continue
            seen.add(key)
            lines.append(line)

        return self._join_paragraphs(lines)

    def _normalize(self, line: str):
        line = re.sub(r"\s+", " ", line)
        line = re.sub(r"[|]{2,}", "|", line)
        return line.strip()

    def _is_useful(self, line: str):
        if len(line) < 4:
            return False
        if line.lower() in noise_words:
            return False
        letters = sum(char.isalpha() for char in line)
        symbols = sum(not char.isalnum() and not char.isspace() for char in line)
        if letters == 0 and symbols > 2:
            return False
        if symbols > max(8, letters * 2):
            return False
        return True

    def _join_paragraphs(self, lines: list[str]):
        paragraphs = []
        current = []

        for line in lines:
            if self._looks_like_heading(line) and current:
                paragraphs.append(" ".join(current))
                current = [line]
            elif line.endswith((".", "?", "!", ";", ":")):
                current.append(line)
                paragraphs.append(" ".join(current))
                current = []
            else:
                current.append(line)

        if current:
            paragraphs.append(" ".join(current))

        return "\n\n".join(paragraphs)

    def _looks_like_heading(self, line: str):
        return len(line) < 90 and (line.istitle() or line.isupper() or line.endswith(":"))
