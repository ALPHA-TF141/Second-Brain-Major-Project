"""
The missing write path - graph construction for the knowledge graph.
=====================================================================
Before this module existed, ``graph_nodes`` and ``graph_edges`` were READ by
five components (retrieval boost, gap detection, importance scoring, forgetting,
clustering) and written by NOTHING. Every fresh database therefore reported an
empty graph, and the paper had to admit that "graph augmentation was not
meaningfully exercised".

This module is the writer. For each ingested memory it materialises:

    node  memory:<id>        node_type="memory"
    node  <concept>          node_type="concept"     (shared across memories)
    edge  memory:<id> -> concept      relationship_type="mentions"
    edge  concept -> concept          relationship_type=<predicate>

Concept nodes are global and deduplicated by (node_type, name), which is what
makes the graph a graph: two memories that mention "python" are connected
through one shared node, and a query that names "python" can reach the Java
memory through the temporal predicate edge that links them.

Extraction has two backends, and the choice is recorded rather than assumed:

    rule    deterministic, dependency-free: token entities + the repo's existing
            temporal fact patterns as triples. This is what the published
            numbers use, because it needs no model download and reproduces
            byte-identically on any machine.
    spacy   en_core_web_sm named entities, noun chunks, and subject-verb-object
            triples. Better recall when the model is installed.

Set GRAPH_EXTRACTOR=rule|spacy|auto (default auto: spacy when importable).
``graph_builder.extractor`` reports which backend actually ran.
"""
from __future__ import annotations

import os
import re
import math
from collections import Counter
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

# Same stopword policy as the benchmark tokeniser, so graph entities and
# retrieval tokens agree about what counts as a term.
STOP = {
    "the", "and", "for", "with", "from", "that", "this", "what", "which", "when",
    "have", "has", "was", "were", "are", "you", "your", "not", "but", "all",
    "can", "will", "am", "is", "are", "my", "me", "i", "on", "in", "to", "of",
    "about", "currently", "now", "still", "any", "do", "does", "did", "must",
    "should", "uses", "use", "using", "used", "their", "there", "then", "than",
    "also", "into", "over", "very", "much", "more", "most", "been", "being",
}

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+.#-]{2,}")

# Predicates that describe a state, and therefore link two concepts in a way a
# query can traverse ("learning python" -> "focused on java").
_STATEFUL = {"current_focus", "current_project", "using", "prefers", "status"}


# --------------------------------------------------------------------- backends
_SPACY_STATE: Any = None


def _spacy():
    """Load en_core_web_sm once. Returns None when unavailable."""
    global _SPACY_STATE
    if _SPACY_STATE is not None:
        return _SPACY_STATE or None
    try:
        import spacy  # noqa: F401
        _SPACY_STATE = spacy.load("en_core_web_sm")
    except Exception:
        _SPACY_STATE = False
    return _SPACY_STATE or None


def extractor_mode() -> str:
    """Which backend will actually be used: 'spacy' or 'rule'."""
    requested = (os.getenv("GRAPH_EXTRACTOR") or "auto").strip().lower()
    if requested == "rule":
        return "rule"
    if requested == "spacy":
        return "spacy" if _spacy() is not None else "rule"
    return "spacy" if _spacy() is not None else "rule"


def _clean(token: str) -> str:
    return (token or "").strip().lower().strip(".,;:!?()[]\"'")


def _rule_entities(text: str) -> List[str]:
    out = []
    for raw in _TOKEN_RE.findall(text or ""):
        token = _clean(raw)
        if len(token) < 3 or token in STOP:
            continue
        out.append(token)
    return out


def _rule_triples(text: str) -> List[Tuple[str, str, str]]:
    """
    Triples from the temporal fact extractor that already exists in this repo.

    Reusing it rather than re-parsing means the graph and the temporal layer can
    never disagree about what the subject of a sentence was.
    """
    triples: List[Tuple[str, str, str]] = []
    try:
        from app.research.temporal import temporal_knowledge_graph

        for fact in temporal_knowledge_graph.extract_facts(text, use_neural=False):
            if fact.get("negated"):
                continue  # a retraction is not an asserted edge
            subject = _clean(fact.get("subject") or "user")
            predicate = _clean(fact.get("predicate") or "related_to")
            obj = _clean(fact.get("object") or "")
            if obj and len(obj) >= 3:
                triples.append((subject, predicate, obj))
    except Exception:
        pass
    return triples


def _spacy_entities(text: str) -> List[str]:
    nlp = _spacy()
    if nlp is None:
        return _rule_entities(text)
    doc = nlp(text or "")
    ents = {_clean(ent.text) for ent in doc.ents}
    ents |= {_clean(chunk.root.lemma_) for chunk in doc.noun_chunks
             if not chunk.root.is_stop and len(chunk.root.text) > 2}
    return [e for e in ents if e and len(e) >= 3 and e not in STOP]


def _spacy_triples(text: str) -> List[Tuple[str, str, str]]:
    nlp = _spacy()
    if nlp is None:
        return _rule_triples(text)
    doc = nlp(text or "")
    triples: List[Tuple[str, str, str]] = []
    for token in doc:
        if token.pos_ != "VERB":
            continue
        subjects = [c for c in token.children if c.dep_ in ("nsubj", "nsubjpass")]
        objects = [c for c in token.children if c.dep_ in ("dobj", "attr", "oprd")]
        for prep in [c for c in token.children if c.dep_ == "prep"]:
            objects += [c for c in prep.children if c.dep_ == "pobj"]
        for subject in subjects:
            for obj in objects:
                subj, pred, ob = _clean(subject.lemma_), _clean(token.lemma_), _clean(obj.lemma_)
                if len(subj) >= 2 and len(ob) >= 3:
                    triples.append((subj, pred, ob))
    return triples


def extract_entities(text: str) -> List[str]:
    return _spacy_entities(text) if extractor_mode() == "spacy" else _rule_entities(text)


def extract_triples(text: str) -> List[Tuple[str, str, str]]:
    return _spacy_triples(text) if extractor_mode() == "spacy" else _rule_triples(text)


# ---------------------------------------------------------------------- builder
class GraphBuilder:
    """Writes memory/concept nodes and mentions/predicate edges."""

    memory_prefix = "memory:"

    # ------------------------------------------------------------------ helper
    @staticmethod
    def _node(db, node_type: str, name: str, *, memory_id: Optional[int] = None,
              at: Optional[datetime] = None):
        from app.models.graph import GraphNode

        node = (db.query(GraphNode)
                  .filter(GraphNode.node_type == node_type, GraphNode.name == name)
                  .first())
        if node is None:
            node = GraphNode(node_type=node_type, name=name, memory_id=memory_id,
                             frequency=1, first_seen=at or datetime.utcnow(),
                             last_seen=at or datetime.utcnow())
            db.add(node)
            db.flush()
            return node, True

        node.frequency = (node.frequency or 0) + 1
        node.last_seen = at or datetime.utcnow()
        if memory_id is not None and node.memory_id is None:
            node.memory_id = memory_id
        return node, False

    @staticmethod
    def _edge(db, source_id: int, target_id: int, relationship: str,
              *, at: Optional[datetime] = None, source: str = "auto",
              strength: float = 0.5):
        from app.models.graph import GraphEdge

        if source_id == target_id:
            return None
        edge = (db.query(GraphEdge)
                  .filter(GraphEdge.source_node_id == source_id,
                          GraphEdge.target_node_id == target_id,
                          GraphEdge.relationship_type == relationship)
                  .first())
        if edge is None:
            edge = GraphEdge(source_node_id=source_id, target_node_id=target_id,
                             relationship_type=relationship, strength_score=strength,
                             frequency=1, source=source)
            db.add(edge)
            db.flush()
            return edge

        edge.frequency = (edge.frequency or 0) + 1
        edge.strength_score = min(1.0, (edge.strength_score or 0.5) + 0.05)
        return edge

    # -------------------------------------------------------------------- write
    def build_memory(self, db, memory_id: int, title: str, content: str,
                     *, at: Optional[datetime] = None, commit: bool = False) -> Dict[str, int]:
        """
        Materialise one memory into the graph. Idempotent: re-running over the
        same memory bumps frequency instead of duplicating rows.
        """
        text = f"{title or ''} {content or ''}"
        entities = []
        seen = set()
        for entity in extract_entities(text):
            if entity not in seen:
                seen.add(entity)
                entities.append(entity)
        triples = extract_triples(text)

        memory_node, _ = self._node(db, "memory", f"{self.memory_prefix}{memory_id}",
                                    memory_id=memory_id, at=at)

        concept_nodes: Dict[str, Any] = {}
        for entity in entities:
            node, _created = self._node(db, "concept", entity, at=at)
            concept_nodes[entity] = node
            self._edge(db, memory_node.id, node.id, "mentions", at=at, source="auto", strength=0.6)

        predicate_edges = 0
        for subject, predicate, obj in triples:
            subj_node = concept_nodes.get(subject) or self._node(db, "concept", subject, at=at)[0]
            obj_node = concept_nodes.get(obj) or self._node(db, "concept", obj, at=at)[0]
            # a concept-to-concept edge only means something if both ends are
            # real nodes; the memory->concept edges already cover co-occurrence
            if subj_node.id == obj_node.id:
                continue
            self._edge(db, subj_node.id, obj_node.id, predicate, at=at,
                       source="temporal" if predicate in _STATEFUL else "auto",
                       strength=0.7 if predicate in _STATEFUL else 0.5)
            predicate_edges += 1

        self._refresh_importance(db, list(concept_nodes.values()))
        if commit:
            db.commit()
        return {"entities": len(concept_nodes), "triples": predicate_edges}

    @staticmethod
    def _refresh_importance(db, nodes: Sequence[Any]) -> None:
        """Concept importance = normalised frequency across the graph."""
        from app.models.graph import GraphNode

        try:
            top = db.query(GraphNode.frequency).order_by(GraphNode.frequency.desc()).first()
            ceiling = max(1, int(top[0])) if top else 1
        except Exception:
            ceiling = 1
        for node in nodes:
            try:
                node.importance_score = min(1.0, (node.frequency or 1) / ceiling)
            except Exception:
                pass

    def build_all(self, db, memories: Iterable[Any], commit: bool = True) -> Dict[str, int]:
        """Build graph rows for an iterable of (id, title, content, created_at)."""
        total_entities = 0
        total_triples = 0
        count = 0
        for memory in memories:
            if isinstance(memory, dict):
                mid = memory["id"]
                title = memory.get("title") or ""
                content = memory.get("content") or ""
                at = memory.get("created_at")
            else:  # ORM Memory row
                mid = memory.id
                title = getattr(memory, "title", "") or ""
                content = getattr(memory, "content", "") or ""
                at = getattr(memory, "created_at", None)
            outcome = self.build_memory(db, mid, title, content, at=at)
            total_entities += outcome["entities"]
            total_triples += outcome["triples"]
            count += 1
        if commit:
            db.commit()
        return {"memories": count, "entities": total_entities, "triples": total_triples}

    # --------------------------------------------------------------------- read
    @staticmethod
    def clear(db, memory_ids: Optional[Iterable[int]] = None, commit: bool = True) -> int:
        """
        Remove graph rows for the given memories, then prune orphaned concepts.

        Scoped on purpose: the benchmark must never delete the user's own graph.
        """
        from app.models.graph import GraphEdge, GraphNode

        query = db.query(GraphNode)
        if memory_ids is not None:
            ids = list(memory_ids)
            if not ids:
                return 0
            names = [f"memory:{mid}" for mid in ids]
            query = query.filter(GraphNode.name.in_(names), GraphNode.node_type == "memory")

        nodes = query.all()
        removed = 0
        for node in nodes:
            db.query(GraphEdge).filter(
                (GraphEdge.source_node_id == node.id) | (GraphEdge.target_node_id == node.id)
            ).delete(synchronize_session=False)
            db.delete(node)
            removed += 1

        # concepts that lost every edge are dead weight in the next expansion
        for node in db.query(GraphNode).filter(GraphNode.node_type == "concept").all():
            linked = db.query(GraphEdge).filter(
                (GraphEdge.source_node_id == node.id) | (GraphEdge.target_node_id == node.id)
            ).count()
            if not linked:
                db.delete(node)
        if commit:
            db.commit()
        return removed

    @staticmethod
    def stats(db) -> Dict[str, Any]:
        """Graph size and connectivity - the numbers a paper has to report."""
        from app.models.graph import GraphEdge, GraphNode

        nodes = db.query(GraphNode).all()
        edges = db.query(GraphEdge).all()
        by_type = Counter(node.node_type for node in nodes)
        edge_types = Counter(edge.relationship_type for edge in edges)

        degree = Counter()
        for edge in edges:
            degree[edge.source_node_id] += 1
            degree[edge.target_node_id] += 1

        memory_nodes = [n for n in nodes if n.node_type == "memory"]
        connected = [n for n in memory_nodes if degree.get(n.id, 0) > 0]

        return {
            "extractor": extractor_mode(),
            "nodes": len(nodes),
            "edges": len(edges),
            "nodes_by_type": dict(by_type),
            "edges_by_type": dict(edge_types.most_common(12)),
            "mean_degree": round(sum(degree.values()) / max(1, len(nodes)), 3),
            "memory_nodes": len(memory_nodes),
            "connected_memory_fraction": round(len(connected) / max(1, len(memory_nodes)), 3),
        }

    # ---------------------------------------------------------------- retrieval
    def expand_scores(self, db, query: str, candidate_ids: Optional[Iterable[int]] = None,
                      *, hops: int = 1, seed_weight: float = 1.0,
                      hop_weight: float = 0.5) -> Dict[int, float]:
        """
        Entity-overlap graph expansion (GraphRAG-style), replacing the old
        degree-only boost.

        Query -> matching concept nodes -> their neighbourhood -> the memories
        those nodes touch. A direct hit scores `seed_weight`; a node reached by
        traversing a predicate edge scores `hop_weight`. Scores are normalised to
        [0,1] so they can be fused with a lexical prior.
        """
        from app.models.graph import GraphEdge, GraphNode

        scope = set(candidate_ids) if candidate_ids is not None else None
        query_entities = set(extract_entities(query))
        if not query_entities:
            return {}

        nodes = db.query(GraphNode).all()
        if not nodes:
            return {}
        by_id = {node.id: node for node in nodes}

        # seed: concept nodes whose name matches a query entity
        seeds = set()
        for node in nodes:
            if node.node_type != "concept":
                continue
            name = (node.name or "").lower()
            if not name:
                continue
            if name in query_entities or any(
                entity == name or (len(entity) > 3 and entity in name) for entity in query_entities
            ):
                seeds.add(node.id)
        if not seeds:
            return {}

        adjacency: Dict[int, Set[int]] = {}
        for edge in db.query(GraphEdge).all():
            adjacency.setdefault(edge.source_node_id, set()).add(edge.target_node_id)
            adjacency.setdefault(edge.target_node_id, set()).add(edge.source_node_id)

        # Rarity weighting. A concept every memory mentions ("dataset") carries no
        # discriminative signal; one that only two memories mention ("aqi") does.
        # Without this the expansion returns a flat 1.0 for every seeded memory,
        # which cannot reorder anything and made the graph look inert.
        memory_node_count = sum(1 for n in nodes if n.node_type == "memory")
        documents: Dict[int, int] = {}
        for node_id in seeds:
            documents[node_id] = sum(
                1 for neighbour in adjacency.get(node_id, ())
                if by_id.get(neighbour) is not None
                and by_id[neighbour].node_type == "memory"
            )
        total_docs = max(1, memory_node_count)
        idf = {
            node_id: math.log((1.0 + total_docs) / (1.0 + documents[node_id])) + 1.0
            for node_id in seeds
        }

        weights: Dict[int, float] = {node_id: seed_weight * idf[node_id] for node_id in seeds}
        frontier = set(seeds)
        for depth in range(hops):
            next_frontier: Set[int] = set()
            for node_id in frontier:
                for neighbour in adjacency.get(node_id, ()):
                    if neighbour in weights:
                        continue
                    next_frontier.add(neighbour)
            for node_id in next_frontier:
                weights[node_id] = hop_weight / (depth + 1)
            frontier = next_frontier

        scores: Dict[int, float] = {}
        for node_id, weight in weights.items():
            node = by_id.get(node_id)
            if node is None:
                continue
            # concept -> the memories that mention it
            memory_node_ids = [node_id] if node.node_type == "memory" else adjacency.get(node_id, set())
            for memory_node_id in memory_node_ids:
                memory_node = by_id.get(memory_node_id)
                if memory_node is None or memory_node.node_type != "memory":
                    continue
                if not (memory_node.name or "").startswith(self.memory_prefix):
                    continue
                try:
                    memory_id = int(memory_node.name.split(":", 1)[1])
                except (IndexError, ValueError):
                    continue
                if scope is not None and memory_id not in scope:
                    continue
                scores[memory_id] = max(scores.get(memory_id, 0.0), weight)

        if not scores:
            return {}
        ceiling = max(scores.values())
        return {mid: value / ceiling for mid, value in scores.items()}


graph_builder = GraphBuilder()
