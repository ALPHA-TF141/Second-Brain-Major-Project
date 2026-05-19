"""Relationship detection between entities for knowledge graph"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DetectedRelationship:
    """Represents a detected relationship between entities"""
    source: str
    target: str
    relationship_type: str
    strength: float  # 0-1
    reasoning: str
    detected_at: datetime


class RelationshipDetector:
    """Detect relationships between entities"""

    # Define relationship patterns
    RELATIONSHIP_PATTERNS = {
        "depends_on": {
            "keywords": ["depends on", "requires", "needs", "based on", "uses", "built with"],
            "strength": 0.9
        },
        "related_to": {
            "keywords": ["related to", "associated with", "connected to", "involves"],
            "strength": 0.7
        },
        "follows": {
            "keywords": ["after learning", "following", "after mastering", "then learned"],
            "strength": 0.85
        },
        "similar_to": {
            "keywords": ["similar to", "like", "comparable to", "alternative to"],
            "strength": 0.75
        },
        "extends": {
            "keywords": ["extends", "builds on", "advanced version of", "next level"],
            "strength": 0.8
        },
        "implements": {
            "keywords": ["implements", "uses to implement", "implements using"],
            "strength": 0.88
        }
    }

    # Predefined entity relationships based on domain knowledge
    KNOWN_RELATIONSHIPS = {
        ("python", "fastapi"): {"type": "implements", "strength": 0.95},
        ("fastapi", "backend"): {"type": "depends_on", "strength": 0.95},
        ("python", "django"): {"type": "implements", "strength": 0.95},
        ("python", "tensorflow"): {"type": "implements", "strength": 0.95},
        ("tensorflow", "machine learning"): {"type": "implements", "strength": 0.9},
        ("pytorch", "machine learning"): {"type": "implements", "strength": 0.9},
        ("machine learning", "nlp"): {"type": "related_to", "strength": 0.85},
        ("nlp", "ocr"): {"type": "related_to", "strength": 0.75},
        ("ocr", "tesseract"): {"type": "implements", "strength": 0.95},
        ("rag", "semantic search"): {"type": "depends_on", "strength": 0.9},
        ("semantic search", "embeddings"): {"type": "depends_on", "strength": 0.95},
        ("embeddings", "machine learning"): {"type": "implements", "strength": 0.9},
        ("react", "frontend"): {"type": "implements", "strength": 0.95},
        ("next.js", "react"): {"type": "depends_on", "strength": 0.9},
        ("docker", "kubernetes"): {"type": "related_to", "strength": 0.8},
        ("neo4j", "knowledge graph"): {"type": "implements", "strength": 0.95},
        ("websocket", "real-time"): {"type": "implements", "strength": 0.9},
        ("rest api", "backend"): {"type": "implements", "strength": 0.9},
    }

    def __init__(self):
        """Initialize relationship detector"""
        pass

    def detect_relationships(self, entities: List[str], context: str = "") -> List[DetectedRelationship]:
        """Detect relationships between a set of entities"""
        relationships = []

        # Check known relationships
        for i, source in enumerate(entities):
            for target in entities[i + 1:]:
                rel = self._check_known_relationship(source, target, context)
                if rel:
                    relationships.append(rel)

        # Check contextual relationships in text
        if context:
            relationships.extend(self._detect_contextual_relationships(entities, context))

        # Check temporal relationships (learning progression)
        relationships.extend(self._detect_temporal_relationships(entities))

        # Deduplicate and score
        relationships = self._aggregate_relationships(relationships)

        return relationships

    def _check_known_relationship(
        self,
        source: str,
        target: str,
        context: str = ""
    ) -> Optional[DetectedRelationship]:
        """Check if two entities have a known relationship"""
        # Normalize names
        source_lower = source.lower().strip()
        target_lower = target.lower().strip()

        # Check both directions
        key1 = (source_lower, target_lower)
        key2 = (target_lower, source_lower)

        rel_data = None
        actual_source, actual_target = source, target

        if key1 in self.KNOWN_RELATIONSHIPS:
            rel_data = self.KNOWN_RELATIONSHIPS[key1]
        elif key2 in self.KNOWN_RELATIONSHIPS:
            rel_data = self.KNOWN_RELATIONSHIPS[key2]
            actual_source, actual_target = target, source

        if rel_data:
            reasoning = f"Known relationship: {actual_source} {rel_data['type']} {actual_target}"
            if context:
                reasoning += f" (context: {context[:50]}...)"

            return DetectedRelationship(
                source=actual_source,
                target=actual_target,
                relationship_type=rel_data["type"],
                strength=rel_data["strength"],
                reasoning=reasoning,
                detected_at=datetime.utcnow()
            )

        return None

    def _detect_contextual_relationships(
        self,
        entities: List[str],
        context: str
    ) -> List[DetectedRelationship]:
        """Detect relationships based on context/text analysis"""
        relationships = []
        context_lower = context.lower()

        for rel_type, pattern_info in self.RELATIONSHIP_PATTERNS.items():
            keywords = pattern_info["keywords"]
            base_strength = pattern_info["strength"]

            for keyword in keywords:
                if keyword in context_lower:
                    # Find entities near this keyword
                    for i, source in enumerate(entities):
                        for target in entities[i + 1:]:
                            # Check proximity in text
                            source_pos = context_lower.find(source.lower())
                            target_pos = context_lower.find(target.lower())
                            keyword_pos = context_lower.find(keyword)

                            if source_pos != -1 and target_pos != -1 and keyword_pos != -1:
                                # Calculate proximity score
                                distance = abs(source_pos - target_pos)
                                proximity_score = max(0, 1 - (distance / 1000))

                                if proximity_score > 0.3:
                                    strength = base_strength * proximity_score

                                    relationships.append(DetectedRelationship(
                                        source=source,
                                        target=target,
                                        relationship_type=rel_type,
                                        strength=strength,
                                        reasoning=f"Contextual: '{keyword}' near both entities",
                                        detected_at=datetime.utcnow()
                                    ))

        return relationships

    def _detect_temporal_relationships(self, entities: List[str]) -> List[DetectedRelationship]:
        """Detect learning progression relationships"""
        relationships = []

        # Learning progressions
        progressions = [
            (["python"], ["machine learning"], 0.8),
            (["machine learning"], ["deep learning"], 0.85),
            (["nlp"], ["semantic search"], 0.8),
            (["ocr"], ["nlp"], 0.75),
            (["rest api"], ["websocket"], 0.7),
        ]

        for prerequisites, followups, strength in progressions:
            has_prereq = any(e.lower() in [p.lower() for p in prerequisites] for e in entities)
            has_followup = any(e.lower() in [f.lower() for f in followups] for e in entities)

            if has_prereq and has_followup:
                for prereq in prerequisites:
                    for followup in followups:
                        if prereq.lower() in [e.lower() for e in entities]:
                            if followup.lower() in [e.lower() for e in entities]:
                                relationships.append(DetectedRelationship(
                                    source=next(e for e in entities if e.lower() == prereq.lower()),
                                    target=next(e for e in entities if e.lower() == followup.lower()),
                                    relationship_type="follows",
                                    strength=strength,
                                    reasoning="Learning progression pattern detected",
                                    detected_at=datetime.utcnow()
                                ))

        return relationships

    def _aggregate_relationships(
        self,
        relationships: List[DetectedRelationship]
    ) -> List[DetectedRelationship]:
        """Deduplicate and aggregate relationships"""
        aggregated = {}

        for rel in relationships:
            key = (rel.source.lower(), rel.target.lower(), rel.relationship_type)

            if key not in aggregated:
                aggregated[key] = rel
            else:
                # Keep the one with higher strength
                if rel.strength > aggregated[key].strength:
                    aggregated[key] = rel

        return list(aggregated.values())

    def calculate_relationship_strength(
        self,
        source: str,
        target: str,
        co_occurrence_count: int = 1,
        proximity: float = 1.0,
        semantic_similarity: float = 0.5
    ) -> float:
        """Calculate relationship strength based on multiple factors"""
        # Base strength from co-occurrence
        co_occurrence_strength = min(co_occurrence_count / 10, 1.0)

        # Normalize factors
        combined = (co_occurrence_strength + proximity + semantic_similarity) / 3

        # Apply weighting
        strength = min(combined * 1.2, 1.0)  # Cap at 1.0

        return strength

    def filter_weak_relationships(
        self,
        relationships: List[DetectedRelationship],
        threshold: float = 0.5
    ) -> List[DetectedRelationship]:
        """Filter out relationships below strength threshold"""
        return [r for r in relationships if r.strength >= threshold]

    def get_relationship_subgraph(
        self,
        central_entity: str,
        relationships: List[DetectedRelationship],
        depth: int = 2
    ) -> Dict[str, List[DetectedRelationship]]:
        """Get a subgraph around a central entity"""
        subgraph = {}
        processed = set()

        def collect_relationships(entity: str, current_depth: int):
            if current_depth == 0 or entity in processed:
                return

            processed.add(entity)
            entity_rels = [
                r for r in relationships
                if r.source.lower() == entity.lower() or r.target.lower() == entity.lower()
            ]

            if entity not in subgraph:
                subgraph[entity] = []
            subgraph[entity].extend(entity_rels)

            for rel in entity_rels:
                next_entity = rel.target if rel.source.lower() == entity.lower() else rel.source
                collect_relationships(next_entity, current_depth - 1)

        collect_relationships(central_entity, depth)
        return subgraph
