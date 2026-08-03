"""Neo4j graph database client for knowledge graph operations"""

import logging
from typing import Any, Dict, List, Optional, Tuple

try:
    from neo4j import GraphDatabase, Session, Transaction, Driver, Result
except ImportError:
    GraphDatabase = None
    Session = Transaction = Driver = Result = Any

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Client for Neo4j graph database operations"""

    def __init__(self, uri: str, username: str, password: str):
        """Initialize Neo4j connection"""
        self.uri = uri
        self.username = username
        self.password = password
        self.driver: Optional[Driver] = None

    def connect(self):
        """Establish connection to Neo4j"""
        if GraphDatabase is None:
            raise RuntimeError("Neo4j Python driver is not installed. Install the optional neo4j package to enable graph persistence.")

        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # Verify connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Connected to Neo4j successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()

    def get_session(self) -> Session:
        """Get a new session"""
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        return self.driver.session()

    # ============ Node Operations ============

    def create_node(
        self,
        name: str,
        node_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a node in the graph"""
        query = """
        CREATE (n:Node {
            name: $name,
            type: $node_type,
            created_at: datetime(),
            properties: $properties
        })
        RETURN n
        """
        try:
            with self.get_session() as session:
                result = session.run(
                    query,
                    name=name,
                    node_type=node_type,
                    properties=properties or {},
                )
                return dict(result.single()["n"])
        except Exception as e:
            logger.error(f"Error creating node: {e}")
            raise

    def get_node(self, name: str, node_type: str) -> Optional[Dict[str, Any]]:
        """Get a node by name and type"""
        query = """
        MATCH (n:Node {name: $name, type: $node_type})
        RETURN n
        """
        try:
            with self.get_session() as session:
                result = session.run(query, name=name, node_type=node_type)
                record = result.single()
                return dict(record["n"]) if record else None
        except Exception as e:
            logger.error(f"Error getting node: {e}")
            return None

    def update_node_frequency(self, name: str, node_type: str, increment: int = 1):
        """Update node frequency (occurrence count)"""
        query = """
        MATCH (n:Node {name: $name, type: $node_type})
        SET n.frequency = COALESCE(n.frequency, 0) + $increment,
            n.last_seen = datetime()
        RETURN n
        """
        try:
            with self.get_session() as session:
                session.run(query, name=name, node_type=node_type, increment=increment)
        except Exception as e:
            logger.error(f"Error updating node frequency: {e}")

    def get_or_create_node(
        self,
        name: str,
        node_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get existing node or create if not exists"""
        query = """
        MERGE (n:Node {name: $name, type: $node_type})
        ON CREATE SET 
            n.created_at = datetime(),
            n.frequency = 1,
            n.properties = $properties
        ON MATCH SET 
            n.frequency = COALESCE(n.frequency, 0) + 1,
            n.last_seen = datetime()
        RETURN n
        """
        try:
            with self.get_session() as session:
                result = session.run(
                    query,
                    name=name,
                    node_type=node_type,
                    properties=properties or {},
                )
                return dict(result.single()["n"])
        except Exception as e:
            logger.error(f"Error in get_or_create_node: {e}")
            raise

    # ============ Edge Operations ============

    def create_relationship(
        self,
        source_name: str,
        source_type: str,
        target_name: str,
        target_type: str,
        relationship_type: str,
        strength: float = 0.5,
        properties: Optional[Dict[str, Any]] = None,
    ):
        """Create a relationship between two nodes"""
        query = f"""
        MATCH (source:Node {{name: $source_name, type: $source_type}})
        MATCH (target:Node {{name: $target_name, type: $target_type}})
        MERGE (source)-[rel:{relationship_type} {{
            strength: $strength,
            created_at: datetime()
        }}]->(target)
        ON CREATE SET rel.frequency = 1, rel.properties = $properties
        ON MATCH SET rel.frequency = COALESCE(rel.frequency, 0) + 1
        RETURN rel
        """
        try:
            with self.get_session() as session:
                session.run(
                    query,
                    source_name=source_name,
                    source_type=source_type,
                    target_name=target_name,
                    target_type=target_type,
                    strength=strength,
                    properties=properties or {},
                )
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")

    def get_relationships(
        self, node_name: str, node_type: str, direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """Get all relationships for a node"""
        if direction == "outgoing":
            query = """
            MATCH (n:Node {name: $name, type: $type})-[rel]->(target)
            RETURN rel, target
            """
        elif direction == "incoming":
            query = """
            MATCH (source)-[rel]->(n:Node {name: $name, type: $type})
            RETURN rel, source as target
            """
        else:  # both
            query = """
            MATCH (n:Node {name: $name, type: $type})-[rel]-(target)
            RETURN rel, target
            """

        try:
            with self.get_session() as session:
                result = session.run(query, name=node_name, type=node_type)
                return [
                    {"relationship": dict(record["rel"]), "node": dict(record["target"])}
                    for record in result
                ]
        except Exception as e:
            logger.error(f"Error getting relationships: {e}")
            return []

    # ============ Path Operations ============

    def shortest_path(
        self, source_name: str, source_type: str, target_name: str, target_type: str
    ) -> List[Dict[str, Any]]:
        """Find shortest path between two nodes"""
        query = """
        MATCH (source:Node {name: $source_name, type: $source_type}),
              (target:Node {name: $target_name, type: $target_type}),
              path = shortestPath((source)-[*]-(target))
        RETURN [node IN nodes(path) | {name: node.name, type: node.type}] as path,
               length(path) as distance
        LIMIT 1
        """
        try:
            with self.get_session() as session:
                result = session.run(
                    query,
                    source_name=source_name,
                    source_type=source_type,
                    target_name=target_name,
                    target_type=target_type,
                )
                record = result.single()
                if record:
                    return {"path": record["path"], "distance": record["distance"]}
                return None
        except Exception as e:
            logger.error(f"Error finding shortest path: {e}")
            return None

    def get_neighbors(
        self, node_name: str, node_type: str, depth: int = 1
    ) -> List[Dict[str, Any]]:
        """Get all neighboring nodes within depth"""
        query = """
        MATCH (n:Node {name: $name, type: $type})-[*1..{depth}]-(neighbor)
        RETURN DISTINCT neighbor
        """.format(depth=depth)

        try:
            with self.get_session() as session:
                result = session.run(query, name=node_name, type=node_type)
                return [dict(record["neighbor"]) for record in result]
        except Exception as e:
            logger.error(f"Error getting neighbors: {e}")
            return []

    # ============ Query Operations ============

    def find_nodes_by_type(self, node_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Find all nodes of a specific type"""
        query = """
        MATCH (n:Node {type: $type})
        RETURN n
        ORDER BY n.frequency DESC
        LIMIT $limit
        """
        try:
            with self.get_session() as session:
                result = session.run(query, type=node_type, limit=limit)
                return [dict(record["n"]) for record in result]
        except Exception as e:
            logger.error(f"Error finding nodes by type: {e}")
            return []

    def find_nodes_by_pattern(self, pattern: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Find nodes matching a pattern"""
        query = """
        MATCH (n:Node)
        WHERE n.name =~ $pattern
        RETURN n
        LIMIT $limit
        """
        try:
            with self.get_session() as session:
                result = session.run(query, pattern=f"(?i).*{pattern}.*", limit=limit)
                return [dict(record["n"]) for record in result]
        except Exception as e:
            logger.error(f"Error finding nodes by pattern: {e}")
            return []

    # ============ Graph Analytics ============

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get overall graph statistics"""
        query = """
        RETURN 
            COUNT(MATCH (n:Node) RETURN n) as node_count,
            COUNT(MATCH ()-[r]->() RETURN r) as edge_count,
            COUNT(MATCH (n:Node) WHERE n.type RETURN n) as type_count
        """
        try:
            with self.get_session() as session:
                result = session.run(query)
                record = result.single()
                return {
                    "total_nodes": record["node_count"] if record else 0,
                    "total_edges": record["edge_count"] if record else 0,
                }
        except Exception as e:
            logger.error(f"Error getting graph stats: {e}")
            return {"total_nodes": 0, "total_edges": 0}

    def find_connected_components(self) -> List[List[Dict[str, Any]]]:
        """Find connected components in the graph"""
        query = """
        CALL algo.unionFind.stream('Node', 'RELATES_TO')
        YIELD nodeId, componentId
        RETURN componentId, collect(algo.getNodeById(nodeId)) as component
        """
        try:
            with self.get_session() as session:
                result = session.run(query)
                return [
                    [dict(node) for node in record["component"]]
                    for record in result
                ]
        except Exception as e:
            logger.warning(f"Neo4j algorithms not available: {e}")
            return []

    def get_node_centrality(self, node_name: str, node_type: str) -> Dict[str, float]:
        """Calculate centrality metrics for a node"""
        query = """
        MATCH (n:Node {name: $name, type: $type})
        RETURN 
            size((n)-[]->()) + size((n)<-[]-()) as degree,
            size(()-[*2]->()-[*2]->(n)) as betweenness_approx
        """
        try:
            with self.get_session() as session:
                result = session.run(query, name=node_name, type=node_type)
                record = result.single()
                if record:
                    return {
                        "degree": record["degree"],
                        "betweenness": record["betweenness_approx"],
                    }
                return {"degree": 0, "betweenness": 0}
        except Exception as e:
            logger.error(f"Error calculating centrality: {e}")
            return {"degree": 0, "betweenness": 0}

    # ============ Bulk Operations ============

    def clear_database(self):
        """Clear all nodes and relationships (use with caution)"""
        query = "MATCH (n) DETACH DELETE n"
        try:
            with self.get_session() as session:
                session.run(query)
            logger.info("Neo4j database cleared")
        except Exception as e:
            logger.error(f"Error clearing database: {e}")

    def create_indexes(self):
        """Create indexes for better query performance"""
        queries = [
            "CREATE INDEX ON :Node(name)",
            "CREATE INDEX ON :Node(type)",
            "CREATE INDEX ON :Node(frequency)",
        ]
        try:
            with self.get_session() as session:
                for query in queries:
                    try:
                        session.run(query)
                    except:
                        pass  # Index might already exist
            logger.info("Neo4j indexes created")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
