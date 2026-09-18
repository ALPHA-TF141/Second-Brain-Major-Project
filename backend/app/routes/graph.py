"""Knowledge graph API routes"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.models.graph import GraphNode, GraphEdge, ConceptCluster, TopicRelationship, LearningProgression
from app.graph.graph_generator import GraphGenerator
from app.graph.neo4j_client import Neo4jClient
from app.clustering.concept_clusterer import ConceptClusterer
from app.recommendations.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/graph", tags=["graph"])

# Global Neo4j client (initialized at startup)
neo4j_client: Optional[Neo4jClient] = None


def initialize_neo4j():
    """Initialize Neo4j client"""
    global neo4j_client
    neo4j_client = Neo4jClient(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="password"
    )
    try:
        neo4j_client.connect()
        neo4j_client.create_indexes()
    except Exception as e:
        logger.warning(f"Neo4j not available: {e}")
        neo4j_client = None


# ============ Graph Management ============

@router.post("/generate")
def generate_knowledge_graph(
    limit: int = 1000,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Generate knowledge graph with seamless fallback"""
    try:
        if neo4j_client:
            generator = GraphGenerator(db, neo4j_client)
            stats = generator.generate_graph_from_memories(limit=limit)
            background_tasks.add_task(generator.recalculate_importance_scores)
            return {"status": "success", "stats": stats}

        return {"status": "success", "message": "Using Memory Vault Knowledge Graph"}
    except Exception as e:
        logger.warning(f"Graph generation notice: {e}")
        return {"status": "success", "message": "Using Memory Vault Knowledge Graph"}


@router.post("/update-session/{session_id}")
def update_graph_from_session(
    session_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Update graph with memories from a session"""
    try:
        if not neo4j_client:
            raise HTTPException(status_code=500, detail="Neo4j not available")

        generator = GraphGenerator(db, neo4j_client)
        stats = generator.update_graph_from_session(session_id)

        return {
            "status": "success",
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error updating graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Node Operations ============

@router.get("/nodes")
def get_nodes(
    node_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Get graph nodes"""
    try:
        query = db.query(GraphNode)

        if node_type:
            query = query.filter(GraphNode.node_type == node_type)

        nodes = query.order_by(
            GraphNode.importance_score.desc()
        ).limit(limit).all()

        if nodes:
            return [{
                "id": n.id,
                "name": n.name,
                "type": n.node_type,
                "importance": n.importance_score,
                "frequency": n.frequency,
                "last_seen": n.last_seen.isoformat() if n.last_seen else None
            } for n in nodes]

        # Seamless Memory Vault Fallback
        import json
        from app.agents.vault_agent import vault_agent
        if vault_agent.graph_file.exists():
            data = json.loads(vault_agent.graph_file.read_text(encoding="utf-8"))
            vault_nodes = []
            for n in data.get("nodes", []):
                vault_nodes.append({
                    "id": n.get("id"),
                    "name": n.get("label", n.get("id")),
                    "type": n.get("domain", "concept").lower(),
                    "importance": 0.95 if n.get("priority") == "high" else 0.75,
                    "frequency": 1,
                    "last_seen": data.get("updated_at")
                })
            return vault_nodes[:limit]
        return []

    except Exception as e:
        logger.error(f"Error getting nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}")
def get_node_detail(
    node_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Get node details with relationships"""
    try:
        node = db.query(GraphNode).filter(GraphNode.id == node_id).first()

        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        # Get incoming and outgoing edges
        incoming = db.query(GraphEdge).filter(GraphEdge.target_node_id == node_id).all()
        outgoing = db.query(GraphEdge).filter(GraphEdge.source_node_id == node_id).all()

        return {
            "id": node.id,
            "name": node.name,
            "type": node.node_type,
            "description": node.description,
            "importance": node.importance_score,
            "frequency": node.frequency,
            "created_at": node.created_at.isoformat(),
            "last_seen": node.last_seen.isoformat(),
            "incoming_edges": [{
                "source_id": e.source_node_id,
                "relationship_type": e.relationship_type,
                "strength": e.strength_score
            } for e in incoming],
            "outgoing_edges": [{
                "target_id": e.target_node_id,
                "relationship_type": e.relationship_type,
                "strength": e.strength_score
            } for e in outgoing]
        }

    except Exception as e:
        logger.error(f"Error getting node: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/search/{query}")
def search_nodes(
    query: str,
    node_type: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Search for nodes by name"""
    try:
        q = db.query(GraphNode).filter(GraphNode.name.ilike(f"%{query}%"))

        if node_type:
            q = q.filter(GraphNode.node_type == node_type)

        nodes = q.limit(limit).all()

        return [{
            "id": n.id,
            "name": n.name,
            "type": n.node_type,
            "importance": n.importance_score
        } for n in nodes]

    except Exception as e:
        logger.error(f"Error searching nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Relationships ============

@router.get("/edges")
def get_edges(
    relationship_type: Optional[str] = None,
    min_strength: float = 0.0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Get graph edges"""
    try:
        query = db.query(GraphEdge)

        if relationship_type:
            query = query.filter(GraphEdge.relationship_type == relationship_type)

        edges = query.filter(
            GraphEdge.strength_score >= min_strength
        ).order_by(
            GraphEdge.strength_score.desc()
        ).limit(limit).all()

        if edges:
            return [{
                "id": e.id,
                "source_id": e.source_node_id,
                "target_id": e.target_node_id,
                "relationship_type": e.relationship_type,
                "strength": e.strength_score,
                "frequency": e.frequency
            } for e in edges]

        # Seamless Memory Vault Fallback
        import json
        from app.agents.vault_agent import vault_agent
        if vault_agent.graph_file.exists():
            data = json.loads(vault_agent.graph_file.read_text(encoding="utf-8"))
            vault_edges = []
            for idx, e in enumerate(data.get("edges", [])):
                vault_edges.append({
                    "id": idx + 1,
                    "source_id": e.get("source"),
                    "target_id": e.get("target"),
                    "relationship_type": e.get("label", "relates_to"),
                    "strength": 0.85,
                    "frequency": 1
                })
            return vault_edges[:limit]
        return []

    except Exception as e:
        logger.error(f"Error getting edges: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/neighbors/{node_id}")
def get_node_neighbors(
    node_id: int,
    depth: int = 1,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Get neighboring nodes"""
    try:
        node = db.query(GraphNode).filter(GraphNode.id == node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        neighbors = []
        visited = {node_id}
        current_level = [node_id]

        for _ in range(depth):
            next_level = []

            for current_id in current_level:
                # Get adjacent nodes
                edges = db.query(GraphEdge).filter(
                    (GraphEdge.source_node_id == current_id) |
                    (GraphEdge.target_node_id == current_id)
                ).all()

                for edge in edges:
                    neighbor_id = edge.target_node_id if edge.source_node_id == current_id else edge.source_node_id

                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        next_level.append(neighbor_id)

                        neighbor = db.query(GraphNode).filter(GraphNode.id == neighbor_id).first()
                        if neighbor:
                            neighbors.append({
                                "id": neighbor.id,
                                "name": neighbor.name,
                                "type": neighbor.node_type,
                                "importance": neighbor.importance_score,
                                "relationship_type": edge.relationship_type,
                                "strength": edge.strength_score
                            })

            current_level = next_level

        return neighbors

    except Exception as e:
        logger.error(f"Error getting neighbors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Clustering ============

@router.post("/clustering/similarity")
def cluster_by_similarity(
    threshold: float = 0.6,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Cluster nodes by similarity"""
    try:
        clusterer = ConceptClusterer(db)
        clusters = clusterer.cluster_by_similarity(threshold=threshold)

        return {
            "clusters_created": len(clusters),
            "clusters": [{
                "id": c.id,
                "name": c.name,
                "size": c.size,
                "cohesion": c.cohesion_score
            } for c in clusters]
        }

    except Exception as e:
        logger.error(f"Error clustering: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clusters")
def get_clusters(
    limit: int = 50,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Get all clusters"""
    try:
        clusters = db.query(ConceptCluster).order_by(
            ConceptCluster.size.desc()
        ).limit(limit).all()

        return [{
            "id": c.id,
            "name": c.name,
            "primary_topic": c.primary_topic,
            "size": c.size,
            "cohesion": c.cohesion_score,
            "node_count": len(c.node_ids) if c.node_ids else 0
        } for c in clusters]

    except Exception as e:
        logger.error(f"Error getting clusters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clusters/{cluster_id}")
def get_cluster_detail(
    cluster_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Get cluster details"""
    try:
        cluster = db.query(ConceptCluster).filter(ConceptCluster.id == cluster_id).first()

        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")

        # Get nodes in cluster
        nodes = db.query(GraphNode).filter(GraphNode.id.in_(cluster.node_ids or [])).all()

        return {
            "id": cluster.id,
            "name": cluster.name,
            "primary_topic": cluster.primary_topic,
            "size": cluster.size,
            "cohesion": cluster.cohesion_score,
            "nodes": [{
                "id": n.id,
                "name": n.name,
                "type": n.node_type,
                "importance": n.importance_score
            } for n in nodes]
        }

    except Exception as e:
        logger.error(f"Error getting cluster: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Recommendations ============

@router.get("/recommendations/related-topics/{topic}")
def recommend_related_topics(
    topic: str,
    limit: int = 5,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Get related topics"""
    try:
        engine = RecommendationEngine(db)
        recommendations = engine.recommend_related_topics(topic, limit=limit)

        return {
            "topic": topic,
            "recommendations": recommendations
        }

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations/next-topics")
def recommend_next_topics(
    learned_topics: List[str],
    limit: int = 5,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Get next topics to learn"""
    try:
        engine = RecommendationEngine(db)
        recommendations = engine.recommend_next_learning_topics(learned_topics, limit=limit)

        return {
            "learned_topics": learned_topics,
            "recommendations": recommendations
        }

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/forgotten")
def recommend_forgotten_concepts(
    days_threshold: int = 30,
    limit: int = 5,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Get forgotten concepts to revisit"""
    try:
        engine = RecommendationEngine(db)
        recommendations = engine.recommend_forgotten_concepts(days_threshold=days_threshold, limit=limit)

        return recommendations

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/related-memories/{memory_id}")
def recommend_related_memories(
    memory_id: int,
    limit: int = 5,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Get memories related to a specific memory"""
    try:
        engine = RecommendationEngine(db)
        recommendations = engine.recommend_related_memories(memory_id, limit=limit)

        return {
            "memory_id": memory_id,
            "related_memories": recommendations
        }

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/learning-gaps")
def get_learning_gaps(
    limit: int = 5,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Get learning gaps"""
    try:
        engine = RecommendationEngine(db)
        gaps = engine.get_learning_gaps(limit=limit)

        return {"learning_gaps": gaps}

    except Exception as e:
        logger.error(f"Error getting learning gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/learning-path")
def get_learning_path(
    start_topic: str,
    end_topic: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Get learning path between topics"""
    try:
        engine = RecommendationEngine(db)
        path = engine.get_learning_path(start_topic, end_topic)

        return path

    except Exception as e:
        logger.error(f"Error getting learning path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Statistics ============

@router.get("/stats")
def get_graph_stats(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    """Get graph statistics"""
    try:
        total_nodes = db.query(GraphNode).count()
        if total_nodes > 0:
            total_edges = db.query(GraphEdge).count()
            total_clusters = db.query(ConceptCluster).count()

            # Get node type distribution
            node_types = {}
            for node_type in ["concept", "technology", "framework", "memory", "session", "language"]:
                count = db.query(GraphNode).filter(GraphNode.node_type == node_type).count()
                if count > 0:
                    node_types[node_type] = count

            # Get top nodes
            top_nodes = db.query(GraphNode).order_by(
                GraphNode.importance_score.desc()
            ).limit(10).all()

            return {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "total_clusters": total_clusters,
                "node_types": node_types,
                "top_nodes": [{
                    "name": n.name,
                    "type": n.node_type,
                    "importance": n.importance_score,
                    "frequency": n.frequency
                } for n in top_nodes]
            }

        # Memory Vault Fallback
        import json
        from app.agents.vault_agent import vault_agent
        if vault_agent.graph_file.exists():
            data = json.loads(vault_agent.graph_file.read_text(encoding="utf-8"))
            nodes = data.get("nodes", [])
            edges = data.get("edges", [])
            node_types = {}
            for n in nodes:
                t = n.get("domain", "General")
                node_types[t] = node_types.get(t, 0) + 1
            return {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "total_clusters": len(node_types),
                "node_types": node_types,
                "top_nodes": [{
                    "name": n.get("label", n.get("id")),
                    "type": n.get("domain", "General"),
                    "importance": 0.95 if n.get("priority") == "high" else 0.75,
                    "frequency": 1
                } for n in nodes[:10]]
            }
        return {"total_nodes": 0, "total_edges": 0, "total_clusters": 0, "node_types": {}, "top_nodes": []}

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"total_nodes": 0, "total_edges": 0, "total_clusters": 0, "node_types": {}, "top_nodes": []}


@router.get("/vault")
def get_vault_graph():
    """Get the live persistent GitHub Memory Vault knowledge graph"""
    import json
    from app.agents.vault_agent import vault_agent
    try:
        if vault_agent.graph_file.exists():
            return json.loads(vault_agent.graph_file.read_text(encoding="utf-8"))
        return {"nodes": [], "edges": []}
    except Exception as e:
        return {"nodes": [], "edges": [], "error": str(e)}


@router.get("/vault/cards")
def get_vault_cards(limit: int = 25):
    """Get the latest curated JSON Memory Cards with Hero images and key pointers"""
    import json
    from pathlib import Path
    from app.agents.vault_agent import vault_agent
    cards = []
    cards_root = vault_agent.cards_dir
    if cards_root.exists():
        card_files = sorted(cards_root.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for card_file in card_files[:limit]:
            try:
                cards.append(json.loads(card_file.read_text(encoding="utf-8")))
            except Exception:
                pass
    return cards


@router.post("/vault/sync")
async def sync_vault_now():
    """Immediately commits and pushes all pending memory cards and graph to GitHub"""
    from app.agents.vault_agent import vault_agent
    success = await vault_agent.sync_to_github()
    return {"success": success}


@router.get("/vault/wiki")
def get_compiled_wiki_articles():
    """Get all self-improving compiled wiki articles"""
    from app.agents.wiki_compiler_agent import wiki_compiler
    return wiki_compiler.list_wiki_articles()


@router.get("/vault/wiki/article")
def get_wiki_article_content(path: str = ""):
    """Fetch content of a specific master wiki article"""
    from app.agents.wiki_compiler_agent import wiki_compiler
    target = wiki_compiler.vault_root / path
    if target.exists() and target.is_file():
        return {"content": target.read_text(encoding="utf-8")}
    raise HTTPException(status_code=404, detail="Wiki article not found")


# ============ Proactive Briefing & Deliverable Forge Routes ============

@router.get("/briefing/today")
async def get_daily_executive_briefing(db: Session = Depends(get_db)):
    """Generates or returns today's Jarvis executive morning briefing"""
    from app.agents.insight_agent import insight_agent
    return await insight_agent.generate_daily_briefing(db)


@router.get("/insights/recent")
def get_recent_insights():
    """Returns recent proactive insight collisions"""
    from app.agents.insight_agent import insight_agent
    return insight_agent.recent_insights


@router.post("/deliverables/generate")
async def generate_deliverable_endpoint(payload: dict):
    """Forges an autonomous publication-grade deliverable from captured memory vault cards"""
    from app.agents.deliverable_agent import deliverable_agent
    from app.agents.vault_agent import vault_agent
    import json

    deliv_type = payload.get("deliverable_type", "research_paper")
    topic = payload.get("topic", "General Research")
    user_instructions = payload.get("user_instructions", "")

    # Gather matching or recent cards
    cards = []
    if vault_agent.cards_dir.exists():
        card_files = sorted(vault_agent.cards_dir.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in card_files[:20]:
            try:
                card_data = json.loads(f.read_text(encoding="utf-8"))
                from app.agents.card_schema import JSONMemoryCard
                cards.append(JSONMemoryCard(**card_data))
            except Exception:
                pass

    result = await deliverable_agent.generate_deliverable(
        deliverable_type=deliv_type,
        topic=topic,
        cards=cards,
        user_instructions=user_instructions
    )
    return result


@router.get("/deliverables")
def list_deliverables_endpoint():
    """Lists all forged deliverables"""
    from app.agents.deliverable_agent import deliverable_agent
    return deliverable_agent.list_deliverables()


@router.get("/deliverables/content")
def get_deliverable_content_endpoint(filename: str = ""):
    """Fetches full markdown text of a deliverable"""
    from app.agents.deliverable_agent import deliverable_agent
    target = deliverable_agent.deliverables_dir / filename
    if target.exists():
        return {"content": target.read_text(encoding="utf-8")}
    raise HTTPException(status_code=404, detail="Deliverable not found")

