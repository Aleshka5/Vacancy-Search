# 📡 API Contract Specification — Vacancy-Search

> **Version:** 1.0.0
> **Date:** 2026-08-04
> **Source:** Extracted from Design Specification (§3.1–3.3), enhanced
> **Status:** Accepted

---

## 1. Authentication

### 1.1 Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/google` | — | Redirect to Google OAuth |
| POST | `/api/v1/auth/refresh` | Cookie (Refresh) | Refresh access token |

### 1.2 Token Format

| Token | Location | Algorithm | Expiry |
|-------|----------|-----------|--------|
| Access Token | `Authorization: Bearer <token>` | RS256 | 15 minutes |
| Refresh Token | `HttpOnly Cookie` | RS256 | 30 days |

### 1.3 Refresh Flow

```text
// POST /api/v1/auth/refresh
// Response: 200 OK
// Headers: Set-Cookie: refresh_token=<token>; HttpOnly; Secure; SameSite=Strict

{
  "access_token": "<new_jwt>",
  "refresh_token": "<new_refresh_token>"  // updated if rotated
}
```

---

## 2. Users & LLM Configs

### 2.1 Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/users/me/llm-configs` | JWT | List user's LLM configs |
| POST | `/api/v1/users/me/llm-configs` | JWT | Create LLM config |
| PATCH | `/api/v1/users/me/llm-configs/{id}` | JWT | Update LLM config |
| DELETE | `/api/v1/users/me/llm-configs/{id}` | JWT | Delete LLM config |

### 2.2 Create LLM Config

```json
// POST /api/v1/users/me/llm-configs
{
  "provider": "openai",  // "openai" | "anthropic" | "ollama"
  "model": "gpt-4",
  "host": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "is_default": true
}

// 201 Created
{
  "id": "<uuid>",
  "provider": "openai",
  "model": "gpt-4",
  "host": "https://api.openai.com/v1",
  "is_default": true,
  "created_at": "2026-08-04T12:00:00Z"
}
```

---

## 3. Knowledge Files

### 3.1 Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/knowledge-files` | JWT | Upload MD file (Multipart) |
| GET | `/api/v1/knowledge-files` | JWT | List knowledge files (paginated) |
| GET | `/api/v1/knowledge-files/{id}` | JWT | Get knowledge file metadata |
| DELETE | `/api/v1/knowledge-files/{id}` | JWT | Delete knowledge file |

### 3.2 Upload Request

```
// POST /api/v1/knowledge-files (multipart/form-data)
// Fields:
//   file (binary) — Markdown file content
//   title (string, optional) — Human-readable title
//   description (string, optional) — File description for context selector

// 201 Created
{
  "id": "<uuid>",
  "title": "Experience",
  "description": "Work experience and projects",
  "minio_path": "knowledge/{user_id}/{file_id}.md",
  "file_size_bytes": 4096,
  "created_at": "2026-08-04T12:00:00Z"
}
```

### 3.3 List Response

```json
// GET /api/v1/knowledge-files?page=1&per_page=10
{
  "items": [
    {
      "id": "<uuid>",
      "title": "Experience",
      "description": "Work experience",
      "minio_path": "knowledge/u1/kf1.md",
      "file_size_bytes": 4096,
      "created_at": "2026-08-04T12:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "per_page": 10
}
```

---

## 4. Chats

### 4.1 Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/chats` | JWT | Create chat (with vacancy text) |
| GET | `/api/v1/chats` | JWT | List user's chats (paginated) |
| GET | `/api/v1/chats/{id}` | JWT | Get chat details |
| GET | `/api/v1/chats/{id}/messages` | JWT | List chat messages |
| POST | `/api/v1/chats/{id}/stream` | JWT | SSE — stream agent response |
| POST | `/api/v1/chats/{id}/messages` | JWT | Send message (answer questions) |

### 4.2 Create Chat

```json
// POST /api/v1/chats
{
  "vacancy_text": "Senior Python Developer at Yandex...\n\nRequirements: Python 3.11+, FastAPI, PostgreSQL...",
  "llm_config_id": "<uuid>"  // optional, uses user default if omitted
}

// 201 Created
{
  "id": "<uuid>",
  "title": null,
  "phase": "parsing",
  "created_at": "2026-08-04T12:00:00Z"
}
```

### 4.3 Chat Details Response

```json
// GET /api/v1/chats/{id}
{
  "id": "<uuid>",
  "title": "Vacancy #123",
  "phase": "questioning",
  "vacancy_text": "...",
  "llm_config_id": "<uuid>",
  "created_at": "2026-08-04T12:00:00Z",
  "updated_at": "2026-08-04T12:01:00Z"
}
```

### 4.4 Send Message

```json
// POST /api/v1/chats/{id}/messages
{
  "content": "5 years of Python, 3 years with FastAPI"
}

// 200 OK
{
  "id": "<uuid>",
  "chat_id": "<uuid>",
  "role": "user",
  "content": "5 years of Python, 3 years with FastAPI",
  "token_usage": {"input_tokens": 50, "output_tokens": 0}
}
```

### 4.5 Chat Phases

| Phase | Description |
|-------|-------------|
| `empty` | Chat created, vacancy parsed |
| `parsing` | Vacancy is being parsed by LLM |
| `questioning` | Agent is asking clarifying questions |
| `generated` | Resume/Cover Letter generated (TeX ready) |
| `compiling` | LaTeX compilation in Podman sandbox |
| `published` | Artifact available in MinIO |
| `error` | Error occurred (retryable) |

---

## 5. Artifacts

### 5.1 Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/artifacts/{id}/download` | JWT | Presigned URL or direct download |
| GET | `/api/v1/chats/{id}/artifacts` | JWT | List artifacts for chat |

### 5.2 Artifact Types

| Type | Description |
|------|-------------|
| `resume_pdf` | Generated resume PDF |
| `resume_tex` | Raw LaTeX source |
| `cover_letter_pdf` | Generated cover letter PDF |
| `cover_letter_tex` | Raw cover letter LaTeX source |

### 5.3 List Artifacts

```json
// GET /api/v1/chats/{id}/artifacts
{
  "items": [
    {
      "id": "<uuid>",
      "type": "resume_pdf",
      "minio_path": "artifacts/c1/art1.pdf",
      "file_size_bytes": 245760,
      "created_at": "2026-08-04T12:02:00Z"
    }
  ]
}
```

---

## 6. Admin

### 6.1 Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/admin/users` | JWT + Admin | List all users (paginated) |
| PATCH | `/api/v1/admin/users/{id}/block` | JWT + Admin | Block/unblock user |
| GET | `/api/v1/admin/prompts` | JWT + Admin | List global prompts |
| PUT | `/api/v1/admin/prompts/{name}` | JWT + Admin | Update prompt |

### 6.2 Block User

```json
// PATCH /api/v1/admin/users/{id}/block
{
  "blocked": true
}

// 200 OK
{
  "id": "<uuid>",
  "email": "user@example.com",
  "is_blocked": true,
  "blocked_at": "2026-08-04T12:00:00Z"
}
```

---

## 7. SSE Event Contract

**Endpoint:** `POST /api/v1/chats/{id}/stream`

Events are streamed as standard Server-Sent Events. Each event carries a `correlation_id` (UUID) for tracing.

### 7.1 Event Types

| Event | Description |
|-------|-------------|
| `step_started` | A new processing step begins |
| `status` | Status message with progress info |
| `assistant_delta` | Incremental text content |
| `assistant_message` | Complete assistant message |
| `artifact_created` | New artifact (PDF/TeX) available |
| `done` | Stream completion |
| `error` | Error occurred |

### 7.2 Event Format

```text
event: step_started
data: {"step": "parsing_vacancy", "timestamp": <epoch_ms>, "correlation_id": "<uuid>"}

event: status
data: {"message": "Analyzing stack requirements...", "tokens_used": 150, "correlation_id": "<uuid>"}

event: assistant_delta
data: {"content": "For this vacancy I'm missing information about your experience with ", "correlation_id": "<uuid>"}

event: assistant_message
data: {"content": "Full assistant message text", "message_id": "<uuid>", "correlation_id": "<uuid>"}

event: artifact_created
data: {"artifact_id": "<uuid>", "type": "resume_pdf", "url": "/api/v1/artifacts/<id>/download", "correlation_id": "<uuid>"}

event: done
data: {"message_id": "<uuid>", "total_tokens": 650, "duration_ms": 4500, "correlation_id": "<uuid>"}

event: error
data: {"code": "LLM_TIMEOUT", "message": "Request to OpenAI timed out", "correlation_id": "<uuid>"}
```

### 7.3 Agent Workflow Events

| Step | Node | Events |
|------|------|--------|
| 1 | VacancyParserNode | `step_started` → `assistant_delta` → `assistant_message` |
| 2 | ContextRetrieverNode | `step_started` → `status` |
| 3 | QuestionerNode | `step_started` → `assistant_message` (with questions) |
| 4 | GeneratorNode | `step_started` → `assistant_delta` → `artifact_created` (TeX) |
| 5 | CompilerNode | `step_started` → `status` → `artifact_created` (PDF) |
| 6 | PublisherNode | `step_started` → `done` |

---

## 8. Error Responses

### 8.1 Error Format

All errors follow the JSON format:

```json
{
  "error": {
    "code": "LLM_TIMEOUT",
    "message": "Request to OpenAI timed out after 60s",
    "details": {
      "provider": "openai",
      "model": "gpt-4",
      "retry_after_ms": 5000
    }
  }
}
```

### 8.2 Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request body validation failed |
| `UNAUTHORIZED` | 401 | Invalid or expired token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists (e.g., duplicate config) |
| `LLM_TIMEOUT` | 408 | LLM request timed out |
| `LLM_ERROR` | 502 | LLM provider returned error |
| `COMPILATION_ERROR` | 500 | LaTeX compilation failed |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## 9. Security

| Concern | Mechanism |
|---------|-----------|
| **AuthN** | Google OAuth 2.0, JWT Access (RS256, 15min), Refresh Token (HttpOnly, 30d) |
| **AuthZ** | Middleware checks `is_blocked`, IDOR protection (`user_id == resource.user_id`) |
| **SSE** | JWT in `Authorization` header or query parameter (`?token=<jwt>`) |
| **Secrets** | Fernet/AES encryption for LLM API keys |

## 10. Routing

All API endpoints use a common prefix defined via environment variable:

| ENV Variable | Default | Description |
|--------------|---------|-------------|
| `API_PREFIX` | `/api/v1` | Prefix for all backend API routes |

Both backend (FastAPI) and frontend must use the same `API_PREFIX` for consistent URL routing.

---

*API Contract v1.0 — Extracted from Design Specification, 2026-08-04*
