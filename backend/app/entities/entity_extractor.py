"""Entity extraction from text for knowledge graph nodes"""

import logging
import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents an extracted entity"""
    name: str
    type: str
    confidence: float
    source: str


class EntityExtractor:
    """Extract entities (concepts, technologies, frameworks, etc.) from text"""

    # Predefined technology and framework lists
    PROGRAMMING_LANGUAGES = {
        "python", "javascript", "java", "cpp", "csharp", "php", "ruby", "go",
        "rust", "kotlin", "swift", "typescript", "scala", "erlang", "elixir",
        "clojure", "haskell", "r", "matlab", "perl", "lua", "sql"
    }

    FRAMEWORKS = {
        "fastapi", "django", "flask", "spring", "spring boot", "react", "vue",
        "angular", "next.js", "nuxt", "express", "nest.js", "rails", "laravel",
        "asp.net", "blazor", "terraform", "kubernetes", "docker", "podman"
    }

    TECHNOLOGIES = {
        "neo4j", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "kafka", "rabbitmq", "docker", "kubernetes", "aws", "azure", "gcp",
        "git", "github", "gitlab", "terraform", "ansible", "jenkins"
    }

    ML_FRAMEWORKS = {
        "tensorflow", "pytorch", "scikit-learn", "keras", "transformers",
        "huggingface", "openai", "langchain", "llamaindex", "chromadb",
        "faiss", "weaviate", "pinecone", "milvus"
    }

    CONCEPTS = {
        "machine learning", "deep learning", "nlp", "ocr", "rag", "ner",
        "semantic search", "embeddings", "transformers", "attention",
        "distributed systems", "microservices", "rest api", "websocket",
        "authentication", "authorization", "encryption", "hashing",
        "optimization", "testing", "debugging", "deployment", "monitoring"
    }

    def __init__(self):
        """Initialize entity extractor"""
        self.all_entities = (
            self.PROGRAMMING_LANGUAGES |
            self.FRAMEWORKS |
            self.TECHNOLOGIES |
            self.ML_FRAMEWORKS |
            self.CONCEPTS
        )

    def extract_entities(self, text: str, source: str = "text") -> List[Entity]:
        """Extract all entities from text"""
        entities = []

        # Extract programming languages
        entities.extend(self._extract_pattern_entities(
            text, self.PROGRAMMING_LANGUAGES, "language", 0.95
        ))

        # Extract frameworks
        entities.extend(self._extract_pattern_entities(
            text, self.FRAMEWORKS, "framework", 0.95
        ))

        # Extract technologies
        entities.extend(self._extract_pattern_entities(
            text, self.TECHNOLOGIES, "technology", 0.9
        ))

        # Extract ML frameworks
        entities.extend(self._extract_pattern_entities(
            text, self.ML_FRAMEWORKS, "ml_framework", 0.9
        ))

        # Extract concepts
        entities.extend(self._extract_pattern_entities(
            text, self.CONCEPTS, "concept", 0.85
        ))

        # Extract URLs/websites
        entities.extend(self._extract_urls(text))

        # Extract people (names)
        entities.extend(self._extract_people_names(text))

        # Extract file/document names
        entities.extend(self._extract_filenames(text))

        # Deduplicate and normalize
        entities = self._deduplicate_entities(entities)

        return entities

    def _extract_pattern_entities(
        self,
        text: str,
        entity_list: Set[str],
        entity_type: str,
        confidence: float
    ) -> List[Entity]:
        """Extract entities matching predefined patterns"""
        entities = []
        text_lower = text.lower()

        for entity_name in entity_list:
            # Use word boundaries to find exact matches
            pattern = r'\b' + re.escape(entity_name) + r'\b'
            if re.search(pattern, text_lower, re.IGNORECASE):
                entities.append(Entity(
                    name=entity_name,
                    type=entity_type,
                    confidence=confidence,
                    source="text"
                ))

        return entities

    def _extract_urls(self, text: str) -> List[Entity]:
        """Extract URLs and websites"""
        entities = []
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text, re.IGNORECASE)

        for url in urls:
            # Extract domain name
            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
            if domain_match:
                domain = domain_match.group(1)
                entities.append(Entity(
                    name=domain,
                    type="website",
                    confidence=0.95,
                    source="url"
                ))

        return entities

    def _extract_people_names(self, text: str) -> List[Entity]:
        """Extract potential person names (capitalized words)"""
        entities = []
        # Look for capitalized words that might be names
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b'
        matches = re.findall(name_pattern, text)

        for name in matches:
            # Filter out common words
            if len(name) > 2 and name not in ["The", "This", "That", "And", "But"]:
                entities.append(Entity(
                    name=name,
                    type="person",
                    confidence=0.6,
                    source="text"
                ))

        return entities

    def _extract_filenames(self, text: str) -> List[Entity]:
        """Extract file and document names"""
        entities = []
        # Look for patterns like "file.txt", "document.pdf", etc.
        filename_pattern = r'\b[\w\-]+\.(py|js|java|cpp|txt|pdf|md|json|yaml|yml|sql|csv)\b'
        matches = re.findall(filename_pattern, text, re.IGNORECASE)

        for filename in matches:
            entities.append(Entity(
                name=filename,
                type="document",
                confidence=0.9,
                source="filename"
            ))

        return entities

    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities, keeping highest confidence"""
        seen = {}
        for entity in entities:
            key = (entity.name.lower(), entity.type)
            if key not in seen or entity.confidence > seen[key].confidence:
                seen[key] = entity

        # Return sorted by confidence
        return sorted(seen.values(), key=lambda e: e.confidence, reverse=True)

    def extract_key_topics(self, text: str, top_n: int = 10) -> List[str]:
        """Extract the most important topics from text"""
        entities = self.extract_entities(text)
        
        # Filter high-confidence entities
        high_conf = [e for e in entities if e.confidence >= 0.85]
        
        # Count occurrences in text for importance
        topic_counts = {}
        for entity in high_conf:
            count = len(re.findall(r'\b' + re.escape(entity.name) + r'\b', text, re.IGNORECASE))
            topic_counts[entity.name] = count

        # Sort by count
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in sorted_topics[:top_n]]

    def categorize_entity(self, name: str) -> str:
        """Determine the category of an entity"""
        name_lower = name.lower()

        if name_lower in self.PROGRAMMING_LANGUAGES:
            return "language"
        elif name_lower in self.FRAMEWORKS:
            return "framework"
        elif name_lower in self.TECHNOLOGIES:
            return "technology"
        elif name_lower in self.ML_FRAMEWORKS:
            return "ml_framework"
        elif name_lower in self.CONCEPTS:
            return "concept"
        else:
            return "unknown"

    def get_related_entities(self, entity_name: str) -> Dict[str, List[str]]:
        """Get entities that commonly relate to a given entity"""
        entity_lower = entity_name.lower()
        relations = {}

        # Python-related
        if entity_lower == "python":
            relations["frameworks"] = ["fastapi", "django", "flask"]
            relations["ml_frameworks"] = ["tensorflow", "pytorch", "scikit-learn"]
            relations["technologies"] = ["jupyter", "anaconda", "pip"]

        # FastAPI-related
        elif entity_lower == "fastapi":
            relations["languages"] = ["python"]
            relations["concepts"] = ["rest api", "websocket", "async"]
            relations["technologies"] = ["docker", "kubernetes"]

        # React-related
        elif entity_lower == "react":
            relations["frameworks"] = ["next.js", "vue"]
            relations["languages"] = ["javascript", "typescript"]
            relations["technologies"] = ["node.js", "webpack", "babel"]

        # Machine Learning
        elif entity_lower == "machine learning":
            relations["frameworks"] = ["tensorflow", "pytorch", "scikit-learn"]
            relations["languages"] = ["python"]
            relations["concepts"] = ["deep learning", "neural networks", "optimization"]

        return relations
