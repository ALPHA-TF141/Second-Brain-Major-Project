import hashlib
import re
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, Tuple, Dict, Any

from app.agents.card_schema import JSONMemoryCard


class CurationAgent:
    """Agent that filters duplicates, purges noise/irrelevant content,
    extracts key pointers, prioritizes Science/Tech/Geopolitics/Research,
    and intelligently selects exactly ONE richest "Hero" image per information period.
    """

    TECH_SCIENCE_KEYWORDS = {
        "technology": [
            "ai", "llm", "neural", "gpu", "cuda", "python", "javascript", "react", "fastapi",
            "docker", "kubernetes", "cloud", "api", "architecture", "algorithm", "database",
            "quantum", "compiler", "linux", "kernel", "cybersecurity", "encryption", "server",
            "model", "weights", "inference", "agentic", "electron", "vite", "git", "github",
            "code", "programming", "software", "stack", "frontend", "backend"
        ],
        "science": [
            "physics", "chemistry", "biology", "astronomy", "neuroscience", "genetics",
            "quantum", "relativity", "particle", "atom", "molecule", "energy", "fusion",
            "space", "telescope", "climate", "evolution", "laboratory", "experiment",
            "nature", "cosmos", "scientific"
        ],
        "geopolitics": [
            "geopolitics", "treaty", "sanctions", "economy", "trade", "defense", "military",
            "policy", "diplomacy", "international", "sovereignty", "summit", "nato", "un",
            "semiconductor", "supply chain", "strategic", "india", "global", "security"
        ],
        "research": [
            "paper", "abstract", "methodology", "benchmark", "arxiv", "nature", "ieee",
            "citation", "hypothesis", "empirical", "evaluation", "state-of-the-art", "sota",
            "study", "lecture", "tutorial", "guide"
        ],
    }

    NOISE_PATTERNS = [
        r"^(new tab|about:blank|untitled)$",
        r"^(task manager|settings|file explorer|start)$",
        r"^(loading|sign in|login|password)$",
    ]

    def __init__(self, history_capacity: int = 40):
        self.recent_hashes = deque(maxlen=history_capacity)
        # Active temporal cluster tracking for hero image selection:
        # { topic_key: { "last_seen": datetime, "best_score": float, "card_id": str } }
        self.active_clusters: Dict[str, Dict[str, Any]] = {}

    def compute_info_score(self, text: str, matched_keywords: list, quality_score: float) -> float:
        """Calculates a contextual richness score (0 - 100+):
        - Word density (more information to explain)
        - Science / Tech / Research keywords (high relevance bonus)
        - Structural markers (code blocks, definitions, equations, bullet points)
        - OCR quality score
        """
        words = text.split()
        word_count = len(words)
        kw_bonus = len(matched_keywords) * 15.0

        structure_bonus = 0.0
        # Code or technical syntax bonus
        if any(c in text for c in ["def ", "class ", "import ", "const ", "function ", "=>", "http", "=", "{", "/>"]):
            structure_bonus += 18.0
        # Structured bullet points / lists
        if any(b in text for b in ["•", "-", "1.", "2.", "3.", "*", ":"]):
            structure_bonus += 12.0

        density_score = min(word_count * 0.45, 50.0)
        total = density_score + kw_bonus + structure_bonus + (quality_score * 20.0)
        return round(total, 2)

    def evaluate_and_curate(
        self,
        raw_text: str,
        app_source: str,
        window_title: str,
        session_id: int,
        raw_image_path: Optional[str] = None
    ) -> Optional[Tuple[JSONMemoryCard, bool]]:
        """Evaluates incoming screen capture & OCR text.
        Returns:
            (JSONMemoryCard, is_new_hero_image_chosen: bool) or None if filtered out.
        """
        clean_text = raw_text.strip()

        # Fallback to Window Title if OCR is sparse/empty (common on video streaming & high-contrast web players)
        if len(clean_text) < 25:
            if window_title and len(window_title.strip()) > 6 and not any(re.search(p, window_title.lower()) for p in self.NOISE_PATTERNS):
                clean_text = f"Activity on {app_source}: {window_title}"
            else:
                return None

        # 1. Content hash deduplication
        content_hash = self._compute_hash(clean_text)
        is_exact_dup = content_hash in self.recent_hashes
        self.recent_hashes.append(content_hash)

        # 2. Window title noise filter
        low_title = window_title.strip().lower()
        for pattern in self.NOISE_PATTERNS:
            if re.search(pattern, low_title):
                return None

        # 3. Domain classification & priority scoring
        domain, priority, matched_keywords = self._classify_domain_and_priority(clean_text, window_title)

        # Skip pure low-value entertainment if no substantive concepts
        if domain == "Entertainment" and priority == "low" and len(matched_keywords) == 0:
            return None

        # 4. Calculate information richness score
        info_score = self.compute_info_score(clean_text, matched_keywords, quality_score=0.9 if priority == "high" else 0.75)

        # 5. Temporal Topic Cluster Deduplication (Best-Shot Hero Selection)
        topic_key = self._make_topic_key(app_source, window_title, domain)
        now = datetime.utcnow()
        should_save_image = False

        cluster = self.active_clusters.get(topic_key)
        # Cluster window lasts 5 minutes per continuous topic
        if cluster and (now - cluster["last_seen"]) < timedelta(minutes=5):
            cluster["last_seen"] = now
            if info_score > cluster["best_score"] and not is_exact_dup:
                # This frame has RICHER context & more information than earlier frames!
                cluster["best_score"] = info_score
                should_save_image = True
            else:
                should_save_image = False
        else:
            # New topic or new time period: initialize cluster & elect as hero
            should_save_image = not is_exact_dup
            self.active_clusters[topic_key] = {
                "last_seen": now,
                "best_score": info_score,
                "card_id": ""
            }

        # 6. Extract Key Pointers and Entities
        key_pointers = self._extract_key_pointers(clean_text, window_title)
        if not key_pointers:
            key_pointers = [window_title] if window_title else [clean_text[:120]]

        entities = self._extract_entities(clean_text, matched_keywords)
        summary = self._generate_summary(clean_text, domain, window_title)
        card_id = f"card_{now.strftime('%Y%m%d_%H%M%S_%f')[:19]}"

        card = JSONMemoryCard(
            id=card_id,
            timestamp=now.isoformat() + "Z",
            domain=domain,
            priority=priority,
            quality_score=0.95 if priority == "high" else 0.8,
            app_source=app_source,
            window_title=window_title,
            topic=matched_keywords[0].title() if matched_keywords else self._topic_from_title(window_title, domain),
            summary=summary,
            key_pointers=key_pointers,
            entities=entities,
            tags=list(set([domain.lower(), app_source.lower().replace('.exe', '')] + matched_keywords[:4])),
            raw_ocr_excerpt=clean_text[:400],
            hero_image=None,
            hero_image_info_score=info_score
        )

        return card, should_save_image

    def _make_topic_key(self, app_source: str, window_title: str, domain: str) -> str:
        norm_title = re.sub(r"\b\d{1,2}:\d{2}\b", "", window_title)
        norm_title = " ".join(norm_title.lower().split()[:6])
        return f"{app_source.lower()}_{domain.lower()}_{norm_title}"

    def _compute_hash(self, text: str) -> str:
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

        best_domain = max(scores, key=scores.get)
        highest_score = scores[best_domain]

        if highest_score >= 2:
            return best_domain, "high", found_keywords
        elif highest_score == 1:
            return best_domain, "medium", found_keywords

        # Check for browser/video consumption
        if any(app in combined for app in ["youtube", "github", "stackoverflow", "arxiv", "nature"]):
            return "Technology", "medium", ["web_knowledge"]

        return "General", "medium", found_keywords

    def _extract_key_pointers(self, text: str, title: str) -> list[str]:
        lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 25]
        if not lines:
            sentences = re.split(r"(?<=[.!?])\s+", text)
            lines = [s.strip() for s in sentences if len(s.strip()) > 25]

        pointers = []
        for line in lines:
            cleaned = re.sub(r"^[•\-\*0-9\.]+\s*", "", line).strip()
            if len(cleaned) > 20 and cleaned not in pointers:
                pointers.append(cleaned[:180])
            if len(pointers) >= 5:
                break

        if not pointers and title:
            pointers.append(title[:160])

        return pointers

    def _extract_entities(self, text: str, matched_keywords: list) -> list[str]:
        entities = set(k.title() for k in matched_keywords[:6])
        proper_nouns = re.findall(r"\b[A-Z][a-zA-Z0-9_\-]{3,}\b", text)
        for noun in proper_nouns[:8]:
            if noun.lower() not in {"this", "that", "there", "about", "from", "with", "have", "video", "youtube", "chrome"}:
                entities.add(noun)
        return list(entities)[:8]

    def _topic_from_title(self, title: str, domain: str) -> str:
        cleaned = re.sub(r"(\s*-\s*(youtube|google chrome|visual studio code|mozilla firefox|microsoft edge))", "", title, flags=re.I)
        return cleaned[:45].strip() if cleaned.strip() else domain

    def _generate_summary(self, text: str, domain: str, title: str) -> str:
        words = text.split()[:40]
        preview = " ".join(words)
        if len(preview) < len(text):
            preview += "..."
        clean_title = re.sub(r"(\s*-\s*(youtube|google chrome|visual studio code|mozilla firefox))", "", title, flags=re.I).strip()
        return f"[{domain}] {clean_title or 'Activity'}: {preview}"


curation_agent = CurationAgent()
