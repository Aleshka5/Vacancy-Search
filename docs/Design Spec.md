# 🏗️ Design Specification — Vacancy-Search

> **Version:** 1.0.0
> **Date:** 2026-08-04
> **Source:** Master Document (§6), ADR-001 through ADR-006, Data Models.md, Flow Spec.md
> **Status:** Accepted

---

## 1. Architecture Solutions

### 1.1 Clean Architecture

**Decision:** Strict Clean Architecture (ADR-001). No DDD concepts (Aggregate Roots, Domain Events).

```
┌─────────────────────────────────────────────┐
│           Presentation Layer                │
│  (FastAPI Routers, SSE, JWT, Pydantic)     │
└────────────┬───────────────────────────────┘
             │ depends on
┌────────────▼───────────────────────────────┐
│           Application Layer                │
│  (Use Cases, DTOs, Orchestration)         │
└────────────┬───────────────────────────────┘
             │ depends on
┌────────────▼───────────────────────────────┐
│           Domain Layer                     │
│  (Entities, Value Objects, Interfaces)     │
│  NO external dependencies                  │
└────────────────────────────────────────────┘
             ▲
             │ implements
┌────────────┴───────────────────────────────┐
│           Infrastructure Layer             │
│  (PostgreSQL, MinIO, LangGraph, Podman)    │
└────────────────────────────────────────────┘
```

**Rules:**
- Dependencies point **inwards** — infrastructure implements domain interfaces.
- Domain is pure — no SQLAlchemy, FastAPI, MinIO references.
- Application orchestrates — never calls infrastructure directly.
- Presentation handles HTTP/SSE only.

### 1.2 Streaming Protocol

**Decision:** Server-Sent Events (ADR-002) over SSE for agent streaming.

- Simpler than WebSocket — single direction, native to HTTP/REST.
- Event types: `step_started`, `status`, `assistant_delta`, `assistant_message`, `artifact_created`, `done`.
- Correlation ID (UUID) propagated through all layers.

### 1.3 Storage Strategy

**Decision:** MinIO for blobs, PostgreSQL for metadata (ADR-003).

- File content → MinIO (MD files, TeX, PDF, templates).
- Metadata → PostgreSQL (paths, relationships, state).
- No file content in DB columns.

### 1.4 LaTeX Sandbox

**Decision:** Podman sandbox with `--network=none`, CPU/RAM limits (ADR-004, ADR-006).

- `PodmanLatexCompiler` — never execute LaTeX directly.
- Isolation prevents RCE via crafted `.tex` files.

### 1.5 Agent Architecture

**Decision:** LangGraph StateGraph with Skill-based Tool Calling (ADR-005).

- 6 nodes: VacancyParser, ContextRetriever, Questioner, Generator, Compiler, Publisher.
- Knowledge files act as skills for dynamic context selection (RAG on descriptions).

---

## 2. Modules

### 2.1 Domain Module (`backend/domain/`)

Pure Python — no external dependencies.

| Module | Contents |
|--------|----------|
| `entities/` | `User`, `Chat`, `Message`, `Artifact`, `Vacancy`, `KnowledgeFile`, `LatexTemplate`, `LLMConfig`, `GlobalPrompt` |
| `interfaces/` | `IUserRepository`, `IChatRepository`, `IMinioStorage`, `ILLMProvider`, `ILatexCompiler`, `IArtifactRepository` |
| `value_objects/` | `ChatPhase`, `ArtifactType`, `LLMProvider`, `MessageRole`, `Role` |

### 2.2 Application Module (`backend/application/`)

Use Cases — orchestrate domain objects via interfaces.

| Use Case | Purpose |
|----------|---------|
| `CreateChatUseCase` | Create chat, optionally generate title |
| `UploadKnowledgeFileUseCase` | Upload MD → MinIO, persist metadata |
| `UploadLatexTemplateUseCase` | Upload `.tex` → MinIO, persist metadata |
| `ParseVacancyUseCase` | Call VacancyParserNode, create Vacancy entity |
| `AskQuestionsUseCase` | Route to QuestionerNode, collect answers |
| `GenerateResumeUseCase` | Generate TeX → compile → save artifact |
| `GenerateCoverLetterUseCase` | Same flow, different prompt |
| `StreamAgentUseCase` | Async generator for SSE events |
| `ListUserChatsUseCase` | Paginated chat list |
| `DownloadArtifactUseCase` | Generate presigned MinIO URL |

### 2.3 Infrastructure Module (`backend/infrastructure/`)

Implementations of domain interfaces.

| Component | Details |
|-----------|---------|
| `repositories/` | `PostgresUserRepository`, `PostgresChatRepository`, `MinioStorage`, `PostgresArtifactRepository` |
| `llm/` | `OpenAIClient`, `AnthropicClient`, `OllamaClient`, `LLMProviderRegistry` |
| `agent/` | `LangGraphAgent` (StateGraph definition), `VacancyParserNode`, `ContextRetrieverNode`, `QuestionerNode`, `GeneratorNode`, `CompilerNode`, `PublisherNode` |
| `latex/` | `PodmanLatexCompiler` |
| `auth/` | `GoogleOAuthHandler`, `JWTHandler` (RS256) |
| `storage/` | `MinioClient` (presigned URLs, multipart upload) |

### 2.4 Presentation Module (`backend/presentation/`)

FastAPI routers and HTTP handlers.

| Component | Details |
|-----------|---------|
| `routers/` | Auth, Chats, Knowledge, Artifacts, LLMConfig, Admin |
| `sse/` | SSE event generator (`SSEGenerator`) |
| `dependencies/` | JWT auth, current user, admin check |
| `schemas/` | Pydantic request/response schemas |

### 2.5 Config Module (`backend/config/`)

| Component | Details |
|-----------|---------|
| `settings.py` | ENV-based settings (Pydantic BaseSettings) |
| `env/` | `.env.example`, environment-specific overrides |
| `minio/` | Bucket definitions |

---

## 3. Contracts

### 3.1 REST API Contracts

#### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/google` | — | Redirect to Google OAuth |
| POST | `/api/v1/auth/refresh` | Cookie (Refresh) | Refresh access token |

#### Users & LLM

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/users/me/llm-configs` | JWT | List user's LLM configs |
| POST | `/api/v1/users/me/llm-configs` | JWT | Create LLM config |
| PATCH | `/api/v1/users/me/llm-configs/{id}` | JWT | Update LLM config |
| DELETE | `/api/v1/users/me/llm-configs/{id}` | JWT | Delete LLM config |

#### Knowledge

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/knowledge-files` | JWT | Upload MD file (Multipart) |
| GET | `/api/v1/knowledge-files` | JWT | List knowledge files |
| GET | `/api/v1/knowledge-files/{id}` | JWT | Get knowledge file metadata |
| DELETE | `/api/v1/knowledge-files/{id}` | JWT | Delete knowledge file |

#### Chats

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/chats` | JWT | Create chat (with vacancy text) |
| GET | `/api/v1/chats` | JWT | List user's chats (paginated) |
| GET | `/api/v1/chats/{id}` | JWT | Get chat details |
| GET | `/api/v1/chats/{id}/messages` | JWT | List chat messages |
| POST | `/api/v1/chats/{id}/stream` | JWT | SSE — stream agent response |
| POST | `/api/v1/chats/{id}/messages` | JWT | Send message (answer questions) |

#### Artifacts

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/artifacts/{id}/download` | JWT | Presigned URL or direct download |
| GET | `/api/v1/chats/{id}/artifacts` | JWT | List artifacts for chat |

#### Admin

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/admin/users` | JWT + Admin | List all users |
| PATCH | `/api/v1/admin/users/{id}/block` | JWT + Admin | Block/unblock user |
| GET | `/api/v1/admin/prompts` | JWT + Admin | List global prompts |
| PUT | `/api/v1/admin/prompts/{name}` | JWT + Admin | Update prompt |

### 3.2 SSE Event Contract

Endpoint: `POST /api/v1/chats/{id}/stream`

```text
event: step_started
data: {"step": "parsing_vacancy", "timestamp": <epoch_ms>}

event: status
data: {"message": "Analyzing stack requirements...", "tokens_used": 150}

event: assistant_delta
data: {"content": "For this vacancy I'm missing information about your experience with "}

event: assistant_message
data: {"content": "Full assistant message text", "message_id": "<uuid>"}

event: artifact_created
data: {"artifact_id": "<uuid>", "type": "resume_pdf", "url": "/api/v1/artifacts/<id>/download"}

event: done
data: {"message_id": "<uuid>", "total_tokens": 650, "duration_ms": 4500}

event: error
data: {"code": "LLM_TIMEOUT", "message": "Request to OpenAI timed out"}
```

### 3.3 Request/Response Schemas (Selected)

#### Create Chat

```json
// POST /api/v1/chats
{
  "vacancy_text": "Senior Python Developer at Yandex...",
  "llm_config_id": "uuid"  // optional, uses user default
}

// 201 Created
{
  "id": "uuid",
  "title": null,
  "phase": "parsing"
}
```

#### Upload Knowledge File

```json
// POST /api/v1/knowledge-files (multipart/form-data)
// Fields: file (binary), title (string), description (string)

// 201 Created
{
  "id": "uuid",
  "title": "Experience",
  "description": "Work experience and projects",
  "minio_path": "knowledge/{user_id}/{file_id}.md",
  "file_size_bytes": 4096
}
```

---

## 4. Data Architecture

### 4.1 Entities (9 core + 3 extended)

See **Data Models.md** for full details.

| Entity | Table | Key Fields |
|--------|-------|------------|
| User | `users` | google_id, email, role, is_blocked |
| LLMConfig | `llm_configs` | user_id, provider, host, api_key_encrypted |
| KnowledgeFile | `knowledge_files` | user_id, title, description, minio_path |
| LatexTemplate | `latex_templates` | user_id, name, minio_path |
| Chat | `chats` | user_id, title, phase, llm_config_id |
| Message | `messages` | chat_id, role, content, token_usage (JSONB) |
| Vacancy | `vacancies` | chat_id, raw_text, parsed_data (JSONB), minio_path |
| Artifact | `artifacts` | chat_id, type, minio_path |
| GlobalPrompt | `global_prompts` | name (unique), content, updated_by |
| AgentMessage | `agent_messages` | chat_id, node_name, state (JSONB) |
| AuditLog | `audit_logs` | user_id, action, details (JSONB), created_at |
| UserSettings | `user_settings` | user_id (unique), key, value |

### 4.2 State Machines

#### Chat Phase Transitions

```
EMPTY → PARSING → QUESTIONING → GENERATED → COMPILING → PUBLISHED
  │          │          │              │           │
  ▼          ▼          ▼              ▼           ▼
ERROR   ERROR     ERROR          ERROR        ERROR(TX)
```

- **ERROR**: any error → retry possible
- **ERROR(TX)**: compilation error → requires TeX fix

#### Agent Workflow (LangGraph)

```
[User Message] → VacancyParserNode → ContextRetrieverNode → QuestionerNode
                                                    │
                                                    ▼
                                              GeneratorNode → CompilerNode → PublisherNode
```

### 4.3 Indexing Strategy

| Table | Index | Purpose |
|-------|-------|---------|
| `users` | `idx_users_google_id` | Unique lookup by Google ID |
| `users` | `idx_users_email` | Unique lookup by email |
| `chats` | `idx_chats_user_id` | User's chat list |
| `messages` | `idx_messages_chat_id` | Chat message ordering |
| `knowledge_files` | `idx_kf_user_id` | User's knowledge files |
| `global_prompts` | `idx_gp_name` | Unique prompt lookup |

### 4.4 MinIO Buckets

| Bucket | Purpose | Path Pattern |
|--------|---------|--------------|
| `knowledge` | User MD files | `knowledge/{user_id}/{file_id}.md` |
| `templates` | LaTeX templates | `templates/{user_id}/{template_id}.tex` |
| `artifacts` | Generated PDFs/TeX | `artifacts/{chat_id}/{artifact_id}.pdf` |
| `temp` | Temporary files | `temp/{user_id}/{file_id}.{ext}` |

---

## 5. Integrations

### 5.1 External Services

| Service | Purpose | Integration |
|---------|---------|-------------|
| **Google OAuth 2.0** | Authentication | ID Token validation, user creation/update |
| **OpenAI** | LLM provider | REST API, streaming via SSE |
| **Anthropic** | LLM provider | REST API, streaming via SSE |
| **Ollama** | LLM provider | Local/self-hosted, REST API |
| **MinIO** | Object storage | S3-compatible, presigned URLs |
| **PostgreSQL** | Relational DB | Async via SQLAlchemy 2.0 |

### 5.2 Internal Components

| Component | Communicates With | Protocol |
|-----------|-------------------|----------|
| FastAPI ↔ LangGraphAgent | Agent execution | Direct function call (async) |
| FastAPI ↔ PodmanLatexCompiler | LaTeX compilation | Podman CLI / HTTP |
| FastAPI ↔ MinioStorage | Blob operations | S3 protocol (aiohttp) |
| FastAPI ↔ Postgres | Metadata | SQLAlchemy async |

### 5.3 Integration Flows

#### OAuth Login Flow

```
Browser → Google Auth (redirect) → Backend (callback)
                                      ├── Validate ID Token
                                      ├── Create/Update User
                                      ├── Generate JWT (RS256)
                                      └── Set Refresh Token (HttpOnly Cookie)
```

#### Vacancy Generation Flow

```
User sends vacancy text
  → VacancyParserNode (calls LLM)
    → ContextRetrieverNode (reads KnowledgeFile descriptions from DB, fetches content from MinIO)
      → QuestionerNode (forms questions)
        → User answers (via chat messages)
          → GeneratorNode (writes TeX with template)
            → CompilerNode (Podman sandbox, --network=none)
              → PublisherNode (saves Artifact to MinIO + DB)
                → SSE event: artifact_created
```

---

## 6. Security Architecture

| Concern | Mechanism |
|---------|-----------|
| **AuthN** | Google OAuth 2.0, JWT Access (RS256, 15min), Refresh Token (HttpOnly, 30d) |
| **AuthZ** | Middleware checks `is_blocked`, IDOR protection (`user_id == resource.user_id`) |
| **Secrets** | Fernet/AES encryption for LLM API keys |
| **Sandbox** | Podman with `--network=none`, CPU/RAM limits |
| **SSE** | JWT in query parameter or header for stream connections |

---

## 7. Observability

| Aspect | Solution |
|--------|----------|
| **Logging** | Structured JSON via `structlog` |
| **Log Collection** | Promtail → Loki |
| **Tracing** | Correlation ID (UUID) propagated through FastAPI → LangGraph → Podman |
| **Metrics** | OpenTelemetry (future) |

---

## 8. Test Strategy

| Level | Tool | Scope |
|-------|------|-------|
| **Unit** | pytest | Use Cases with mocked infrastructure |
| **Integration** | pytest + testcontainers | Postgres, MinIO, full pipeline |
| **Agent** | pytest + LLM mocks | LangGraph node transitions |
| **E2E** | Playwright | UI flows: chat, streaming, artifacts |

---

## 9. Traceability Matrix

| Requirement | Design Component | Test Case |
|-------------|-----------------|-----------|
| US2.1 (MD Files) | `KnowledgeFile` entity, `MinioStorage`, `UploadKnowledgeFileUseCase` | `test_upload_knowledge_file` |
| US3.3 (Agent Stream) | `StreamAgentUseCase`, `SSEGenerator`, SSE event contract | `test_sse_events_sequence` |
| ADR-004 (Sandbox) | `PodmanLatexCompiler`, `--network=none` | `test_latex_compilation_isolation` |
| US1.1 (OAuth) | `GoogleOAuthHandler`, JWT, Refresh Token | `test_oauth_flow` |
| US3.4 (Cover Letter) | `GenerateCoverLetterUseCase`, `ArtifactType.COVER_LETTER_*` | `test_cover_letter_generation` |

---

## 10. Dependencies Between Docs

| This Document | Referenced In |
|---------------|---------------|
| Architecture → ADR-001, ADR-002, ADR-003, ADR-004, ADR-005, ADR-006 | |
| Modules → Domain entities in Data Models.md | |
| Contracts → API Contract Spec in Master Document (§7) | |
| Data → Data Models.md (full detail) | |
| Integrations → ADR-003 (MinIO), ADR-004 (Podman), ADR-005 (Agent) | |
| Security → Security Spec in Master Document (§8) | |
| Observability → Observability Spec in Master Document (§9) | |
| Test → Test Spec in Master Document (§10) | |

---

*Design Specification v1.0 — Created 2026-08-04*
