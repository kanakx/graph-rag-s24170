# Graph RAG

### Quickstart

```bash
uv sync
```

```bash
docker compose --profile dev --env-file .env.dev up -d
```

- Streamlit Frontend: [http://localhost:8501](http://localhost:8501)
- Neo4j Browser: [http://localhost:7474/browser/](http://localhost:7474/browser/)
- MinIO Console: [http://localhost:9001/browser/uploads](http://localhost:9001/browser/uploads)

## Documentation

## Project Overview

A GraphRAG-based CV/resume knowledge system using Neo4j for structured data storage and retrieval. The system extracts entities from PDF CVs, builds a knowledge graph, and enables natural language querying via a Streamlit chatbot.

## Architecture

- **Frontend**: Streamlit
- **AI Service**: FastAPI with LLM-powered graph extraction and chat
- **Storage**: Neo4j (knowledge graph), MinIO (file storage)
- **LLM**: Azure OpenAI

---

## RAG vs GraphRAG Comparison

### Structural Differences

| Aspect | Traditional RAG | GraphRAG (This Project) |
|--------|----------------|-------------------------|
| **Storage** | Vector embeddings in vector DB | Neo4j nodes/relationships |
| **Retrieval** | Cosine similarity on chunks | Cypher queries + fulltext index |
| **Context** | Flat text snippets | Structured entities with explicit relationships |
| **Query Type** | "Find similar text" | "Traverse connections" |

### Why GraphRAG for CV Data

CVs are inherently relational:
- Person → HAS\_SKILL → Skill
- Person → WORKED\_AT → Company
- Person → STUDIED\_AT → University

Traditional RAG would embed CV text as chunks, losing these explicit connections. GraphRAG preserves them, enabling queries like *"Who has Python experience and worked at a startup?"* through multi-hop traversals.

---

## Metrics

### Retrieval Performance

| Metric | Value | Notes |
|--------|-------|-------|
| Fulltext search latency | ~50-100ms | Using `search_index` |
| Graph expansion latency | ~100-200ms | 5 people, 4 relationship types |
| Context size limit | 8000 chars | Truncated in `retrieve_graph_context` |

### Extraction Quality

| Metric | Observation |
|--------|-------------|
| Node type accuracy | High for Person, Skill, Company; lower for Certification dates |
| Relationship completeness | ~85% of expected HAS\_SKILL edges created |
| False positives | Occasional job titles extracted as Skills |

### Limitations Observed

- LLM extraction quality depends heavily on CV formatting
- Generic queries ("list people") require fallback logic
- No deduplication—same skill from multiple CVs creates duplicate nodes

---

## Key Implementation Decisions

1. **Schema-driven extraction** (`SCHEMA_PROMPT`)—forces consistent node/relationship types
2. **Fallback retrieval**—if fulltext search returns nothing, fetch any 5 people
3. **Explicit source tracking**—`source_id` property links nodes back to original PDF

---

## Conclusions

1. **GraphRAG excels for relational data**—CV entities (skills, companies, education) are naturally connected; a graph captures this better than flat embeddings.

2. **Trade-off: extraction quality vs retrieval quality**—the bottleneck isn't the graph queries, it's the LLM's ability to parse unstructured CVs into clean nodes.

3. **Traditional RAG might suffice for simple search**—if only doing "find CVs mentioning Python", vector similarity is simpler to implement.

4. **Schema design is critical**—poorly defined node types lead to inconsistent graphs. The `SCHEMA_PROMPT` rules (e.g., "Do NOT create Person nodes for companies") directly impact downstream query accuracy.
