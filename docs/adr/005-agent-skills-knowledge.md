# ADR-005: Agent Skills & Knowledge

## Status
**Accepted**

## Date
2026-08-04

## Context
Our LangGraph agent needs to understand and use user-supplied knowledge files (Markdown) during resume generation. The agent must:
- Parse and understand the knowledge files
- Select relevant files for each vacancy
- Use file content as context for LaTeX generation
- Treat knowledge files as "skills" the agent can use

Options considered:
- **RAG with vector embeddings**: Embed knowledge files, retrieve via similarity. Good for large collections but requires embedding model.
- **Description-based selection**: Use file descriptions as "skills" — agent selects based on description relevance. Simpler, no extra model calls.
- **Hybrid approach**: Description for initial selection, then RAG for content extraction.
- **Manual tagging**: User tags files, agent uses tags. Requires user effort.

## Decision
We use a **two-level approach** combining description-based selection with content retrieval:

### Level 1: Description-Based "Skills"
- Each knowledge file has a `description` field (stored in Postgres, not the content).
- The agent analyzes the vacancy text and selects relevant files based on description matching.
- Descriptions serve as "skill declarations" — the agent knows what each file contains.

### Level 2: Content Retrieval
- Selected files are read from MinIO (full content).
- Content is injected into the LLM prompt as context.

### LangGraph Node Flow
```
VacancyParserNode
  ↓
ContextRetrieverNode: Analyze descriptions → select file IDs
  ↓
Read selected files from MinIO
  ↓
QuestionerNode: Formulate questions if data is insufficient
  ↓
GeneratorNode: Inject TEX with context
  ↓
CompilerNode: Compile in Podman sandbox
  ↓
PublisherNode: Save artifact
```

## Consequences
- **Positive:**
  - Simple and efficient — no embedding model needed for selection.
  - User-friendly — descriptions are human-readable and editable.
  - Scalable — can add vector-based RAG later without changing the interface.
  - Descriptions are stored in Postgres (fast access) while content is in MinIO.
- **Negative:**
  - Description quality matters — poor descriptions lead to poor selection.
  - No semantic understanding — relies on keyword/context matching in LLM prompt.
  - For very large knowledge bases (>100 files), description-based selection may need tuning.
- **Rules:**
  - Every knowledge file MUST have a meaningful description.
  - Agent selects files by analyzing descriptions against the vacancy context.
  - Content is read lazily — only selected files are fetched from MinIO.

## Authors
Vacancy-Search Team

## References
- [Master Document §ADR-005](../docs/Master%20Document.md#5-agent-skills--knowledge)
- [Master Document §6: Agent Flow](../docs/Master%20Document.md#3-agent-flow-langgraph)
- [Master Document §13: Prompt Engineering Spec](../docs/Master%20Document.md#13-prompt-engineering-spec)
