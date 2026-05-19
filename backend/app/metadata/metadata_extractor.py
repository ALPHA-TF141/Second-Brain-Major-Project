import re
from collections import Counter


stop_words = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
    "that",
    "have",
    "your",
    "you",
    "are",
    "was",
    "will",
}


class MetadataExtractor:
    def extract_keywords(self, text: str, limit: int = 8):
        words = re.findall(r"[A-Za-z][A-Za-z0-9_+-]{3,}", text)
        counts = Counter(word.lower() for word in words if word.lower() not in stop_words)
        return [word for word, _count in counts.most_common(limit)]

    def quality_score(self, clean_text: str):
        words = clean_text.split()
        if not words:
            return 0
        readable = sum(1 for word in words if any(char.isalpha() for char in word))
        return min(100, int((readable / len(words)) * 100))
