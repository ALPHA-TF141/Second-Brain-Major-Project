import re
from collections import Counter


category_keywords = {
    "coding": {"python", "javascript", "react", "fastapi", "sql", "function", "class", "import", "api"},
    "learning": {"lecture", "study", "chapter", "tutorial", "course", "lesson", "example"},
    "research": {"paper", "article", "abstract", "references", "analysis", "model", "method"},
    "browsing": {"youtube", "browser", "chrome", "edge", "firefox", "search", "video"},
}


class MemoryTagger:
    def tag(self, content: str, topic_label: str = "", source_type: str = "", app_source: str = ""):
        text = f"{topic_label} {source_type} {app_source} {content}".lower()
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]{2,}", text)
        counts = Counter(words)

        tags = set()
        if source_type:
            tags.add(source_type.title())
        if app_source:
            tags.add(app_source.replace(".exe", "").title())
        for word, _count in counts.most_common(12):
            if word not in {"the", "and", "for", "with", "from", "this", "that", "you", "are"}:
                tags.add(word.title())

        return sorted(tags)[:10]

    def category(self, content: str, source_type: str = "", app_source: str = ""):
        text = f"{source_type} {app_source} {content}".lower()
        scores = {}
        for category, keywords in category_keywords.items():
            scores[category] = sum(1 for keyword in keywords if keyword in text)
        best = max(scores, key=scores.get)
        return best if scores[best] else "learning"
