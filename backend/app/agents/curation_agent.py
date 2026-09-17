import hashlib
import re
from datetime import datetime
from collections import deque
from typing import Optional, Tuple

from app.agents.card_schema import JSONMemoryCard


class CurationAgent:
    """Agent that filters duplicates, purges noise/irrelevant content,
    extracts key pointers, and prioritizes Science, Technology, Geopolitics, and Research.
    """

    TECH_SCIENCE_KEYWORDS = {
        "technology": [
            "ai", "llm", "neural", "gpu", "cuda", "python", "javascript", "react", "fastapi",
            "docker", "kubernetes", "cloud", "api", "architecture", "algorithm", "database",
            "quantum", "compiler", "linux", "kernel", "cybersecurity", "encryption", "server",
            "model", "weights", "inference", "agentic", "electron", "vite", "git", "github"
        ],
        "science": [
            "physics", "chemistry", "biology", "astronomy", "neuroscience", "genetics",
            "quantum", "relativity", "particle", "atom", "molecule", "energy", "fusion",
            "space", "telescope", "climate", "evolution", "laboratory", "experiment"
        ],
        "geopolitics": [
            "geopolitics", "treaty", "sanctions", "economy", "trade", "defense", "military",
            "policy", "diplomacy", "international", "sovereignty", "summit", "nato", "un",
            "semiconductor", "supply chain", "strategic"
        ],
        "research": [
            "paper", "abstract", "methodology", "benchmark", "arxiv", "nature", "ieee",
            "citation", "hypothesis", "empirical", "evaluation", "state-of-the-art", "sota"
        ],
    }

    NOISE_PATTERNS = [
        r"^(new tab|about:blank|untitled)$",
        r"^(task manager|settings|file explorer)$",
        r"^(loading|sign in|login|password)$",
    ]

    def __init__(self, history_capacity: int = 40):
        # Keeps recent text hashes for instant deduplication
        self.recent_hashes = deque(maxlen=history_capacity)
        self.recent_titles = deque(maxlen=history_capacity)

    def evaluate_and_curate(
        self,
        raw_text: str,
        app_source: str,
        window_title: str,
        session_id: int
    ) -> Optional[JSONMemoryCard]:
        clean_text = raw_text.strip()
        if len(clean_text) < 25:
            # Too short to be valuable knowledge
            return None

        # 1. Deduplication check
        content_hash = self._compute_hash(clean_text)
        if content_hash in self.recent_hashes:
            return None
        self.recent_hashes.append(content_hash)

        # 2. Window title noise filter
        low_title = window_title.strip().lower()
        for pattern in self.NOISE_PATTERNS:
            if re.search(pattern, low_title):
                return None

        # 3. Domain classification & priority scoring
        domain, priority, matched_keywords = self._classify_domain_and_priority(clean_text, window_title)

        # Skip pure entertainment / repetitive social scrolling if no substantive concepts
        if domain == "Entertainment" and priority == "low" and len(matched_keywords) == 0:
            return None

        # 4. Extract Key Pointers (3-5 crisp bullet points)
        key_pointers = self._extract_key_pointers(clean_text)
        if not key_pointers:
            return None

        # 5. Extract Entities
        entities = self._extract_entities(clean_text, matched_keywords)

        # 6. Generate Summary
        summary = self._generate_summary(clean_text, domain, window_title)

        card_id = f"card_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:19]}"

        return JSONMemoryCard(
            id=card_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            domain=domain,
            priority=priority,
            quality_score=0.9 if priority == "high" else 0.75,
            app_source=app_source,
            window_title=window_title,
            topic=matched_keywords[0].title() if matched_keywords else domain,
            summary=summary,
            key_pointers=key_pointers,
            entities=entities,
            tags=list(set([domain.lower(), app_source.lower()] + matched_keywords[:4])),
            raw_ocr_excerpt=clean_text[:400]
        )

    def _compute_hash(self, text: str) -> str:
        # Normalize whitespace and compute MD5
        normalized = " ".join(text.lower().split()[:60])
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def _classify_domain_and_priority(self, text: str, title: str) -> Tuple[str, str, list]:
        combined = (text + " " + title).lower()
        found_keywords = []

        scores = {"Technology": 0, "Science": 0, "Geopolitics": 0, "Research": 0}

        for domain, kw_list in self.TECH_SCIENCE_KEYWORDS.items():
            for kw in kw_list:
                if re.search(rf"\b{re.escape(kw)}\b", combined):
                    scores[domain.title()] += 2 if kw in title.lower() else 1
                    found_keywords.append(kw)

        # Pick highest scoring domain
        best_domain = max(scores, key=scores.get)
        highest_score = scores[best_domain]

        if highest_score >= 2:
            return best_domain, "high", found_keywords
        elif highest_score == 1:
            return best_domain, "medium", found_keywords

        # Check for social media / video entertainment
        low_app = combined.lower()
        if any(app in low_app for app in ["instagram", "reels", "tiktok", "shorts", "meme"]):
            return "Entertainment", "low", []

        return "General", "medium", found_keywords

    def _extract_key_pointers(self, text: str) -> list[str]:
        # Split into sentences or lines
        lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 30]
        if not lines:
            sentences = re.split(r"(?<=[.!?])\s+", text)
            lines = [s.strip() for s in sentences if len(s.strip()) > 30]

        pointers = []
        for line in lines:
            # Clean up line
            cleaned = re.sub(r"^[•\-\*0-9\.]+\s*", "", line).strip()
            if len(cleaned) > 25 and cleaned not in pointers:
                pointers.append(cleaned[:180])
            if len(pointers) >= 5:
                break

        return pointers if pointers else [text[:160]]

    def _extract_entities(self, text: str, matched_keywords: list) -> list[str]:
        entities = set(k.title() for k in matched_keywords[:6])
        # Find capitalized words (proper nouns)
        proper_nouns = re.findall(r"\b[A-Z][a-zA-Z0-9_\-]{3,}\b", text)
        for noun in proper_nouns[:8]:
            if noun.lower() not in {"this", "that", "there", "about", "from", "with", "have"}:
                entities.add(noun)
        return list(entities)[:8]

    def _generate_summary(self, text: str, domain: str, title: str) -> str:
        words = text.split()[:40]
        preview = " ".join(words)
        if len(preview) < len(text):
            preview += "..."
        return f"[{domain}] {title}: {preview}"


curation_agent = CurationAgent()
