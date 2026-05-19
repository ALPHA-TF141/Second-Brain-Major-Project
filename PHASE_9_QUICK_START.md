# Phase 9 Quick Start Guide

## What's New?

Phase 9 brings the **Knowledge Graph Engine** - a brain-like memory system that:
- ✅ Connects related concepts automatically
- ✅ Tracks learning evolution over time
- ✅ Visualizes your knowledge network
- ✅ Recommends what to learn next
- ✅ Identifies forgotten important concepts
- ✅ Shows learning paths between topics

## 5-Minute Setup

### Step 1: Start Neo4j
```bash
# Using Docker (easiest)
docker run -d --name neo4j \
  -p 7687:7687 \
  -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

### Step 2: Update Backend Config
Edit `backend/app/config.py`:
```python
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"
```

### Step 3: Install Dependencies
```bash
# Python packages
pip install neo4j==5.13.0 networkx==3.1

# Frontend package
npm install reactflow
```

### Step 4: Restart Backend & Frontend
```bash
# Backend
python -m uvicorn app.main:app --reload

# Frontend
npm start
```

### Step 5: Generate Your Knowledge Graph
1. Go to http://localhost:3000/knowledge-graph
2. Click "Generate Graph"
3. Watch as your memories become a connected network!

## What You'll See

### The Graph
- **Nodes**: Concepts, technologies, memories
- **Edges**: Relationships between concepts
- **Size**: Important or frequently mentioned concepts are larger
- **Color**: Same types share colors
  - 🔵 Concepts (Blue)
  - 🟣 Technologies (Purple)
  - 🩷 Frameworks (Pink)
  - 🟠 Languages (Orange)
  - 🟢 Memories (Green)

### Three View Modes
1. **Graph**: Interactive network visualization
2. **Clusters**: Topic groupings
3. **Stats**: Overall metrics

## Key Features

### 1. Interactive Exploration
- Zoom in/out on areas of interest
- Drag nodes to explore
- Click nodes to see details
- Search for concepts

### 2. Smart Filtering
- Filter by type (concept, technology, etc.)
- Show only important nodes (>50% threshold)
- Show only strong relationships (>60% strength)
- Search by name

### 3. Recommendations
- **Related Topics**: What's connected to this concept
- **Next Learning**: What should I learn next?
- **Forgotten Concepts**: Important things I've forgotten
- **Related Memories**: Memories on this topic
- **Learning Path**: How to get from A to B

### 4. Node Details
Click any node to see:
- Type and description
- Importance score
- How many times mentioned
- All connected concepts
- When first seen / last updated

## Example Workflows

### Discover Learning Paths
```
1. Click "Knowledge Graph" in sidebar
2. Search for starting concept (e.g., "Python")
3. Use recommendation: "Next Topics to Learn"
4. Follow the suggested path to explore
```

### Find Related Memories
```
1. Select a memory in your timeline
2. Check "Related Memories" recommendations
3. Click to jump to those memories
```

### Identify Learning Gaps
```
1. View recommendations: "Learning Gaps"
2. These are important topics you haven't fully explored
3. Click recommendations to learn more
```

### Create a Study Plan
```
1. Find a final topic you want to master
2. Use "Learning Path" to see the journey
3. Follow the recommended progression
4. Track your progress through the graph
```

## Performance Tips

### For Large Knowledge Bases (1000+ memories)
- Start with "Generate Graph"
- Then use filters to explore sections
- Click "Cluster Concepts" to group related topics

### For Slow Performance
- Reduce the limit in graph generation (e.g., start with 100)
- Use filters to show fewer nodes
- Clear browser cache if visualization is slow

## Common Questions

### Q: Why is my graph empty?
**A**: You need memories first! Go to the dashboard, let it capture some screenshots, run OCR, and rebuild memories.

### Q: How often should I regenerate the graph?
**A**: After adding new sessions or memories. It's fast and updates the relationships.

### Q: Can I export my graph?
**A**: Currently, you can take screenshots or copy the visualization. Export features coming in future phases!

### Q: What's the difference between nodes and edges?
**A**: 
- **Nodes** = Concepts (Python, FastAPI, etc.)
- **Edges** = Relationships (depends_on, related_to, etc.)

## Advanced Usage

### Understanding Relationship Types
- `depends_on`: Requires knowledge of (e.g., FastAPI depends_on Python)
- `related_to`: Loosely connected (e.g., OCR related_to NLP)
- `follows`: Learning progression (e.g., NLP follows OCR)
- `similar_to`: Alternative approach
- `extends`: Advanced version of
- `implements`: Uses to build

### Importance Scores
- 0-30%: Nice to know, rarely used
- 30-60%: Useful, moderately connected
- 60-90%: Core concepts, frequently mentioned
- 90-100%: Central to your learning

### Strength Scores (Edge Strength)
- 0-30%: Weak connection
- 30-60%: Moderate relationship
- 60-90%: Strong relationship
- 90-100%: Very strong, frequently co-occur

## Troubleshooting

### Neo4j Won't Connect
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# If not running, start it
docker run -d --name neo4j \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

### Graph Generation Is Slow
- Check system resources
- Reduce the limit (generate 100 at a time instead of 1000)
- Add more RAM if using Docker

### Visualization Is Janky
- Reduce the number of nodes shown (use filters)
- Close other browser tabs
- Clear browser cache

## Next Steps

1. **Generate Your Graph** - See your knowledge connections
2. **Explore Clusters** - See how your learning is organized
3. **Use Recommendations** - Discover what to learn next
4. **Track Learning** - Watch the graph grow as you learn more
5. **Find Connections** - See how different areas relate

## Architecture at a Glance

```
Your Memories
    ↓
Entity Extraction
    ↓
Relationship Detection
    ↓
Graph Creation (Neo4j + SQLite)
    ↓
Clustering
    ↓
Importance Scoring
    ↓
Beautiful Interactive Visualization!
```

## Performance Metrics

| Action | Time |
|--------|------|
| Generate graph (100 memories) | ~5 seconds |
| Generate graph (1000 memories) | ~30-60 seconds |
| Search nodes | <100ms |
| Get recommendations | <200ms |
| Render visualization | <500ms |

## System Requirements

**Backend:**
- Python 3.8+
- 2GB RAM (minimum)
- 1GB storage (for database)

**Frontend:**
- Modern browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled

**Graph Database:**
- Neo4j Community Edition (free)
- Docker recommended for easy setup

## Getting Help

For issues or questions:
1. Check the full documentation: `PHASE_9_IMPLEMENTATION.md`
2. Review your browser console for errors
3. Check Neo4j logs: `docker logs neo4j`
4. Verify database connection in FastAPI logs

## What's Coming in Future Phases?

- 🎨 Advanced visualizations (3D, animations)
- 🤖 ML-based recommendations
- 📊 Learning analytics and insights
- 🔄 Collaborative graph sharing
- 📈 Career path recommendations
- 💾 Export to multiple formats
