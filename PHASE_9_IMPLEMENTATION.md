# Phase 9: Knowledge Graph & Brain-like Memory Relationship Engine

## Overview

Phase 9 transforms the Second Brain system from isolated memories into a **connected cognitive network**. It creates an intelligent knowledge graph that understands relationships between concepts, tracks learning evolution, and provides personalized recommendations.

## Architecture

### Backend Components

#### 1. **Neo4j Integration Layer** (`app/graph/neo4j_client.py`)
- Graph database client for querying and updating the knowledge graph
- Node and edge operations (CRUD)
- Path finding algorithms
- Graph analytics and statistics
- Connection management

**Key Features:**
- Create/update nodes with properties
- MERGE operations for idempotent updates
- Relationship management with strength scoring
- BFS for path finding
- Centrality calculations

#### 2. **Entity Extraction System** (`app/entities/entity_extractor.py`)
Automatically extracts entities from memories:
- **Programming Languages**: Python, JavaScript, Java, Rust, etc.
- **Frameworks**: FastAPI, Django, React, Vue, etc.
- **Technologies**: Neo4j, PostgreSQL, Docker, Kubernetes, etc.
- **ML Frameworks**: TensorFlow, PyTorch, scikit-learn, etc.
- **Concepts**: Machine Learning, OCR, RAG, Semantic Search, etc.
- **Other**: URLs, filenames, people names

**Extraction Methods:**
- Pattern matching on predefined entity lists
- URL extraction
- Filename detection
- Person name extraction (capitalized words)
- Deduplication and confidence scoring

#### 3. **Relationship Detection Engine** (`app/relationships/relationship_detector.py`)
Automatically detects connections between entities:

**Relationship Types:**
- `depends_on`: A requires B (e.g., FastAPI depends_on Python)
- `related_to`: General association
- `follows`: Learning progression (e.g., OCR follows NLP)
- `similar_to`: Alternative or equivalent
- `extends`: Advanced version of
- `implements`: Uses to implement

**Detection Methods:**
- Known relationship database (hardcoded domain knowledge)
- Contextual analysis (proximity in text)
- Temporal patterns (learning progressions)
- Semantic similarity

#### 4. **Graph Generation Pipeline** (`app/graph/graph_generator.py`)
Orchestrates entity extraction and graph building:
- Processes memories batch by batch
- Creates nodes for entities
- Establishes relationships
- Links memories to concepts
- Creates memory nodes
- Calculates importance scores

**Process:**
```
Memories → Extract Entities → Detect Relationships → Create Nodes → Create Edges → Build Clusters
```

#### 5. **Concept Clustering** (`app/clustering/concept_clusterer.py`)
Groups related concepts together:
- **Similarity-based clustering**: BFS to find connected components
- **Type-based clustering**: Groups by node type
- **Topic-based clustering**: Infers topics and groups
- **Hierarchical clustering**: Agglomerative approach

**Metrics:**
- Cluster size (node count)
- Cohesion score (internal edge strength)
- Primary topic identification

#### 6. **Recommendation Engine** (`app/recommendations/recommendation_engine.py`)
Generates intelligent recommendations:

**Recommendation Types:**
1. **Related Topics**: Similar concepts in the graph
2. **Next Learning Topics**: Progressive topics to learn
3. **Forgotten Concepts**: High-importance concepts not revisited
4. **Related Memories**: Memories sharing concepts
5. **Learning Gaps**: Under-explored topics connected to learned ones
6. **Learning Paths**: Step-by-step progression from one topic to another

**Scoring:**
- Relationship strength
- Node importance
- Frequency
- Temporal factors (recency)
- Learning progression patterns

#### 7. **Database Models** (`app/models/graph.py`)

**GraphNode**
```python
id, name, node_type, description
memory_id, session_id
frequency, importance_score
first_seen, last_seen, metadata
```

**GraphEdge**
```python
source_node_id, target_node_id
relationship_type, strength_score, frequency
source (auto/semantic/temporal/manual), metadata
```

**ConceptCluster**
```python
name, description, primary_topic
node_ids (list), size, cohesion_score
```

**TopicRelationship**
```python
source_topic, target_topic
co_occurrence_count, learning_progression
strength, first_linked, last_linked
```

**LearningProgression**
```python
topic, level, memory_count, session_count
date, duration_hours, metadata
```

**GraphMetadata**
```python
key-value store for graph statistics
```

### Frontend Components

#### 1. **Knowledge Graph Page** (`src/pages/KnowledgeGraph.jsx`)
Main page with:
- Interactive graph visualization
- Filter panel (type, importance, search)
- Multiple view modes (graph, clusters, stats)
- Toolbar with generation/clustering controls
- Real-time statistics

#### 2. **Graph Visualization** (`src/components/GraphVisualization.jsx`)
React Flow based visualization:
- **Node Rendering**: Sized by frequency, colored by type
- **Edge Rendering**: Width by strength, animated for strong relationships
- **Interactions**: Pan, zoom, drag, click
- **Mini Map**: Overview of graph
- **Legend**: Type color coding
- **Tooltip**: Node details on hover

**Node Types Colors:**
- Concept: Blue
- Technology: Purple
- Framework: Pink
- Language: Orange
- Memory: Green
- Session: Cyan
- Topic: Indigo

#### 3. **Node Details Panel** (`src/components/NodeDetailsPanel.jsx`)
Displays when node is clicked:
- Node metadata (name, type, importance)
- Metrics (frequency, connections)
- Timeline (created, last seen)
- Incoming/outgoing relationships
- Metadata and properties
- Expandable sections

#### 4. **Filter Panel** (`src/components/FilterPanel.jsx`)
Dynamic filtering:
- Search by name
- Filter by node type
- Minimum importance threshold
- Minimum relationship strength
- Reset filters

#### 5. **Recommendation Panel** (`src/components/RecommendationPanel.jsx`)
Shows intelligent suggestions:
- Ranked recommendations
- Reasoning explanations
- Confidence scores
- Quick action buttons
- Related memories/topics

### API Endpoints

#### Graph Management
- `POST /api/graph/generate` - Generate graph from memories
- `POST /api/graph/update-session/{id}` - Update from session
- `POST /api/graph/clustering/similarity` - Cluster by similarity

#### Nodes
- `GET /api/graph/nodes` - List all nodes
- `GET /api/graph/nodes/{id}` - Node details
- `GET /api/graph/nodes/search/{query}` - Search nodes
- `GET /api/graph/neighbors/{id}` - Get neighbors

#### Relationships
- `GET /api/graph/edges` - List edges
- `GET /api/graph/edges?relationship_type=X` - Filter edges

#### Clustering
- `GET /api/graph/clusters` - List clusters
- `GET /api/graph/clusters/{id}` - Cluster details

#### Recommendations
- `GET /api/graph/recommendations/related-topics/{topic}` - Related topics
- `POST /api/graph/recommendations/next-topics` - Next learning topics
- `GET /api/graph/recommendations/forgotten` - Forgotten concepts
- `GET /api/graph/recommendations/related-memories/{id}` - Related memories
- `GET /api/graph/recommendations/learning-gaps` - Learning gaps
- `GET /api/graph/recommendations/learning-path?start=X&end=Y` - Learning path

#### Statistics
- `GET /api/graph/stats` - Graph statistics

## Setup Instructions

### 1. Backend Setup

#### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
# Add to requirements:
neo4j==5.13.0
networkx==3.1
```

#### Neo4j Setup
```bash
# Install Neo4j
# Option 1: Docker
docker run -d --name neo4j \
  -p 7687:7687 \
  -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# Option 2: Local installation
# Download from https://neo4j.com/download/
```

#### Database Initialization
The graph models are automatically created via SQLAlchemy on startup. Neo4j connection is initialized in `app/main.py`:

```python
@app.on_event("startup")
async def on_startup():
    init_database()
    initialize_neo4j()  # Connects to Neo4j
    ...
```

### 2. Frontend Setup

#### Install React Flow (if not already installed)
```bash
cd frontend
npm install reactflow
```

#### CSS Files
All CSS files are included and will be automatically loaded:
- `src/styles/knowledge-graph.css` - Main page
- `src/styles/graph-visualization.css` - Visualization
- `src/styles/filter-panel.css` - Filters
- `src/styles/node-details.css` - Details panel
- `src/styles/recommendation-panel.css` - Recommendations

### 3. Environment Configuration

Update `backend/app/config.py`:
```python
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"
```

## Usage Guide

### 1. Generating the Knowledge Graph

**First Time Setup:**
```bash
# Visit: http://localhost:3000/knowledge-graph
# Click "Generate Graph" button
# This will:
# - Extract entities from all memories
# - Detect relationships between entities
# - Create graph nodes and edges
# - Calculate importance scores
# - Generate concept clusters
```

**Expected Time:**
- For 1,000 memories: ~30-60 seconds

### 2. Exploring the Graph

**Interactive Visualization:**
- **Zoom**: Scroll wheel or pinch
- **Pan**: Click and drag background
- **Move Nodes**: Drag nodes around
- **Select Node**: Click node to see details
- **Double-click**: Auto-fit to node

**View Modes:**
1. **Graph**: Full network visualization
2. **Clusters**: Topic groupings
3. **Stats**: Overall metrics and distributions

### 3. Using Filters

**Search**: Find nodes by name prefix
**Node Type**: Show only specific types (concept, technology, etc.)
**Importance**: Show only high-importance nodes
**Strength**: Show only strong relationships

Example: Show only Python-related concepts with 60%+ importance

### 4. Understanding Node Details

When you click a node, you see:
- **Name & Type**: What the node represents
- **Metrics**: 
  - Importance: How central to your learning
  - Frequency: How many times mentioned
  - Connections: Related nodes
- **Timeline**: When first seen and last revisited
- **Relationships**: What points to/from this node
  - Type: depends_on, related_to, follows, etc.
  - Strength: 0-100% confidence

### 5. Getting Recommendations

**Related Topics**
- Shows concepts connected to a topic
- Click a node to see recommendations

**Next Learning Topics**
- Based on what you've already learned
- Suggests natural progressions

**Forgotten Concepts**
- Important topics you haven't revisited
- Shows days since last seen

**Related Memories**
- Find memories sharing concepts
- Explore connections in your learning

**Learning Path**
- Step-by-step progression from topic A to B
- Shows intermediate concepts to learn

## Examples

### Example 1: Python Learning Progression
```
Python
  ↓ implements
FastAPI
  ↓ related_to
REST APIs
  ↓ follows
WebSockets
  ↓ depends_on
Async Programming
```

### Example 2: Machine Learning Journey
```
Python (start)
  ↓ implements
scikit-learn
  ↓ follows
Deep Learning
  ↓ implements
TensorFlow
  ↓ related_to
Neural Networks
  ↓ follows
Transformers
```

### Example 3: OCR to RAG Pipeline
```
OCR (Document Processing)
  ↓ follows
Text Extraction
  ↓ depends_on
NLP
  ↓ follows
Semantic Understanding
  ↓ implements
Embeddings
  ↓ depends_on
Vector Search
  ↓ related_to
RAG (Retrieval Augmented Generation)
```

## Performance Optimization

### Database Optimization
- Indexes on frequently queried columns
- Proper foreign key relationships
- Batch processing for large imports

### Neo4j Optimization
- Connection pooling
- Query optimization
- Index creation on startup
- Lazy loading of neighbors

### Frontend Optimization
- Virtual scrolling for long lists
- Memoization of components
- Lazy loading of graph data
- Efficient force simulation (React Flow)

## Advanced Features

### 1. Temporal Analysis
- Track when concepts were learned
- See learning acceleration/deceleration
- Identify periods of intense study

### 2. Topic Evolution Tracking
- See how topics evolved over time
- Identify obsolete knowledge
- Track changing interests

### 3. Learning Pattern Detection
- Identify repeated concepts
- Detect learning plateaus
- Find optimal learning sequences

### 4. Semantic Similarity
- Find conceptually similar topics
- Discover hidden connections
- Suggest related fields

## Troubleshooting

### Neo4j Connection Issues
```python
# Check connection
from app.graph.neo4j_client import Neo4jClient
client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
client.connect()
```

### Empty Graph
- Make sure memories exist in database
- Run `/api/graph/generate` endpoint
- Check for entity extraction issues

### Slow Performance
- Reduce limit in graph generation
- Add more indexes in Neo4j
- Optimize relationship queries

## Future Enhancements

1. **Graph Visualization Enhancements**
   - 3D visualization option
   - Animation of graph evolution
   - Heat maps of activity

2. **ML-Based Recommendations**
   - Personalized learning paths
   - Skill gap analysis
   - Career path recommendations

3. **Collaborative Features**
   - Graph sharing
   - Peer learning networks
   - Concept consensus

4. **Export Features**
   - Export graph as image/PDF
   - Learning path export
   - Concept map generation

## API Reference

### Generate Knowledge Graph
```bash
POST /api/graph/generate
{
  "limit": 1000
}

Response:
{
  "status": "success",
  "stats": {
    "nodes_created": 245,
    "edges_created": 1203,
    "clusters_created": 12,
    "errors": 0
  }
}
```

### Get Node Details
```bash
GET /api/graph/nodes/123
{
  "Authorization": "Bearer <token>"
}

Response:
{
  "id": 123,
  "name": "Python",
  "type": "language",
  "importance": 0.92,
  "frequency": 47,
  "incoming_edges": [...],
  "outgoing_edges": [...]
}
```

### Get Recommendations
```bash
GET /api/graph/recommendations/next-topics?learned_topics=python,fastapi

Response:
{
  "learned_topics": ["python", "fastapi"],
  "recommendations": [
    {
      "name": "async/await",
      "type": "concept",
      "score": 0.89,
      "importance": 0.85,
      "reasoning": "Natural learning progression"
    }
  ]
}
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Knowledge Graph Page                                    │ │
│  │  - Graph Visualization (React Flow)                    │ │
│  │  - Filter Panel                                        │ │
│  │  - Node Details                                        │ │
│  │  - Recommendations Panel                               │ │
│  └─────────────────────────────────────────────────────────┘ │
└────────────────────┬─────────────────────────────────────────┘
                     │ HTTP
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                Backend (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Graph API Routes                                     │   │
│  │  - /api/graph/generate                              │   │
│  │  - /api/graph/nodes/...                             │   │
│  │  - /api/graph/recommendations/...                   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Graph Processing                                     │   │
│  │  - Entity Extractor                                 │   │
│  │  - Relationship Detector                            │   │
│  │  - Graph Generator                                  │   │
│  │  - Clustering Engine                                │   │
│  │  - Recommendation Engine                            │   │
│  └──────────────────────────────────────────────────────┘   │
└────────┬─────────────────────────────────────┬───────────────┘
         │                                     │
         ▼                                     ▼
    ┌─────────────┐                    ┌──────────────┐
    │  SQLite DB  │                    │  Neo4j Graph │
    │  (SQL Store)│                    │  (Network)   │
    │             │                    │              │
    │ - Nodes     │                    │ - Nodes      │
    │ - Edges     │                    │ - Edges      │
    │ - Clusters  │                    │ - Paths      │
    │ - Memory    │                    │ - Analytics  │
    │   Assoc.    │                    │              │
    └─────────────┘                    └──────────────┘
```

## Conclusion

Phase 9 transforms the Second Brain into a true cognitive network, capable of understanding relationships between concepts, learning patterns, and providing intelligent guidance. The system transforms isolated memories into an interconnected knowledge graph that mirrors human cognitive structures.

This creates:
- **Understanding**: The system understands how concepts relate
- **Learning**: It can guide learning paths
- **Memory**: It connects related memories
- **Intelligence**: It provides personalized recommendations
