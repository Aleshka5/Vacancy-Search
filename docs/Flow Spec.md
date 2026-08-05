# 🔄 Flow Specification

Describes user flows and transitions between application states. Based on Master Document, ADR and User Stories.

---

## 0. Authentication Flow

### 0.1 Google OAuth Login

```
┌──────────┐     HTTP 302     ┌────────────────┐
│  Browser │ ──────────────►  │  Google Auth   │
└──────────┘                  └────────────────┘
                                  │
                                  │ redirect_uri
                                  ▼
                          ┌────────────────┐
                          │  Backend       │
                          │  OAuth Handler │
                          └────────────────┘
                                  │
                          ┌───────┼───────┐
                          ▼       ▼       ▼
                    ┌────────┐ ┌────────┐ ┌────────┐
                    │ Create │ │ Update │ │  403   │
                    │ User   │ │ User   │ │ Blocked│
                    └────────┘ └────────┘ └────────┘
                          │
                          ▼
                    ┌──────────────┐
                    │ JWT Access   │
                    │ (15 min)     │
                    └──────────────┘
                    ┌──────────────┐
                    │ Refresh      │
                    │ Token (30d)  │
                    │ HttpOnly     │
                    └──────────────┘
```

**Details:**
- `POST /api/v1/auth/google` — redirect to Google OAuth.
- On callback return — ID Token validation, user creation/update.
- **Access Token** (RS256) — in frontend memory (not Cookie), TTL 15 minutes.
- **Refresh Token** — in `HttpOnly, Secure, SameSite=Strict` Cookie, TTL 30 days.
- Blocked users receive `403 Forbidden` on any request.
- When Access Token expires — frontend makes `POST /api/v1/auth/refresh` with Refresh Token.

### 0.2 JWT Session Management

```
┌────────────┐     ┌────────────────┐     ┌──────────────┐
│  Frontend  │────▶│  FastAPI       │────▶│  Redis/DB    │
│  (Token)   │◀────│  Auth Decorator│◀────│  (optional)  │
└────────────┘     └────────────────┘     └──────────────┘
```

- Each protected request includes `Authorization: Bearer ***` in the header.
- Middleware validates signature, expiration, and user block status.
- IDOR protection: each request checks `user_id == resource.user_id`.

---

## 1. Onboarding Flow (First Visit)

```
1. Google Login
       ▼
2. ┌────────────────────────────────────────────────────┐
   │  Welcome Screen                                    │
   │  "Welcome! Let's set up your profile."             │
   └────────────────────────────────────────────────────┘
       ▼
3. ┌────────────────────────────────────────────────────┐
   │  LLM Configuration                                 │
   │  - Provider: OpenAI / Anthropic / Ollama / Custom  │
   │  - Host URL                                        │
   │  - API Key (encrypted in DB)                       │
   │  - "Set as Default"                                │
   └────────────────────────────────────────────────────┘
       ▼
4. ┌────────────────────────────────────────────────────┐
   │  Upload Knowledge Files (MD)                       │
   │ - Drag & drop or file selection                    │
   │ - Limit: MAX_KNOWLEDGE_FILES (ENV, default: 10)    │
   │ - Length: MAX_KNOWLEDGE_FILE_LENGTH (ENV,          │
   │   default: 10000 characters)                       │
   └────────────────────────────────────────────────────┘
       ▼
5. ┌────────────────────────────────────────────────────┐
   │  Upload LaTeX Template                             │
   │  - .tex file                                       │
   │  - Preview in browser                              │
   └────────────────────────────────────────────────────┘
       ▼
6. ┌────────────────────────────────────────────────────┐
   │  Dashboard (Empty State)                           │
   │  "Paste a vacancy text to get started."            │
   └────────────────────────────────────────────────────┘
```

**States:**
- If the user already has data (LLM config, MD files, LaTeX template) — skip steps 3-5.
- Can return to configuration at any time via Settings.

---

## 2. Knowledge Base Flow

### 2.1 User Profile Page — Knowledge Files

```
┌────────────────────────────────────────────────────────────────────┐
│  📝 Knowledge Files                                                │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  LaTeX Template (for resume generation)                      │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │  [ LaTeX input / editor — Monaco or CodeMirror ]       │  │  │
│  │  │                                                        │  │  │
│  │  │  \documentclass{article}                               │  │  │
│  │  │  \begin{document}                                      │  │  │
│  │  │  \title{My Resume}                                     │  │  │
│  │  │  ...                                                   │  │  │
│  │  │  \end{document}                                        │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ─── Knowledge Files ─────────────────────────────────────────     │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  File 1: "Experience"                                      │    │
│  │  Description: "Work experience, projects, achievements"    │    │
│  │  ┌────────────────────────────────────────────────────┐    │    │
│  │  │  [ Markdown textarea with live preview ]           │    │    │
│  │  └────────────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  File 2: "Education"                                       │    │
│  │  Description: "Degrees, courses, certifications"           │    │
│  │  ┌────────────────────────────────────────────────────┐    │    │
│  │  │  [ Markdown textarea with live preview ]           │    │    │
│  │  └────────────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  File 3: "Skills"                                          │    │
│  │  Description: "Technical skills, tools, languages"         │    │
│  │  ┌────────────────────────────────────────────────────┐    │    │
│  │  │  [ Markdown textarea with live preview ]           │    │    │
│  │  └────────────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                    │
│  [+ Add New File]  (disabled if MAX_KNOWLEDGE_FILES reached)       │
│                                                                    │
│  ─── Actions ──────────────────────────────────────────            │
│  [ Save All ]  [ Upload .tex Template ]                            │
└────────────────────────────────────────────────────────────────────┘
```

**Constants (ENV):**
- `MAX_KNOWLEDGE_FILES` — maximum number of MD files (default: 10).
- `MAX_KNOWLEDGE_FILE_LENGTH` — maximum length (number of characters) of one MD file (default: 10000).

**Storage:**
- Each MD file is uploaded to MinIO as a separate object.
- Metadata (`title`, `description`, `minio_path`) — in the `knowledge_files` table.
- LaTeX template — a separate record in `latex_templates`, stored in MinIO.
- Template and MD files are bound to a specific user via `user_id`.

**Agent Skill Selection:**
- The `description` field is used as a skill for dynamic context selection.
- `MAX_KNOWLEDGE_FILE_LENGTH` — maximum length (number of characters) of one MD file.
- Agent (via `ContextRetrieverNode`) analyzes descriptions and selects the necessary files.
- Can use one, several, or all files depending on the request.

---

## 3. Chat Page Flow

### 3.1 Layout

- **Sidebar** — collapsible (button at top).
- **Recent Chats** — loaded from DB (`chats` table, filtered by `user_id`, ordered by `created_at DESC`).
- **New Chat** — creates a new `Chat` entity with empty `title` (generated later).

### 3.2 Chat Interaction Flow

**SSE Streaming Details:**

```
event: step_started
data: {"step": "parsing_vacancy", "timestamp": 1690000000}

event: status
data: {"message": "Analyzing stack requirements...", "tokens_used": 150}

event: status
data: {"message": "Selecting context from knowledge base...", "tokens_used": 420}

event: assistant_delta
data: {"content": "For this vacancy I'm missing information about your experience with "}

event: assistant_delta
data: {"content": " FastAPI and PostgreSQL."}

event: status
data: {"message": "Formulating questions...", "tokens_used": 580}

event: assistant_message
data: {"content": "Full assistant message text", "message_id": "uuid"}

event: done
data: {"message_id": "uuid", "total_tokens": 650, "duration_ms": 4500}
```

**User message:**
- User sends vacancy text or answers questions.
- If data is incomplete — agent asks questions via `QuestionerNode`.
- If all data is collected — user can request Resume or Cover Letter generation.

**AI Agent Flow (LangGraph):**
1. `VacancyParserNode` — parses vacancy (company, stack, requirements).
2. `ContextRetrieverNode` — selects the needed MD files by descriptions (skills), reads them from MinIO.
3. `QuestionerNode` — forms a list of questions if data is insufficient.
4. `GeneratorNode` — writes TeX code based on template and context.
5. `CompilerNode` — sends TeX to Podman Sandbox, receives PDF, uploads to MinIO.
6. `PublisherNode` — saves Artifact to DB, streams `artifact_created`.

---

## 4. Artifact Handling Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  Artifact Lifecycle                                              │
│                                                                  │
│  1. Generation:                                                  │
│     ┌───────────┐    ┌──────────────┐   ┌──────────────────┐     │
│     │  TeX File │───▶│  Podman      │──▶│  PDF File        │     │
│     │  (temp)   │    │  Sandbox     │   │  (MinIO)         │     │
│     └───────────┘    └──────────────┘   └──────────────────┘     │
│                                                                  │
│  2. Storage:                                                     │
│     ┌──────────────────────────────────────────────────────┐     │
│     │  MinIO Bucket: "artifacts"                           │     │
│     │  Path: /{user_id}/{chat_id}/{artifact_id}.pdf        │     │
│     └──────────────────────────────────────────────────────┘     │
│                                                                  │
│  3. Metadata:                                                    │
│     ┌──────────────────────────────────────────────────────┐     │
│     │  Table: artifacts                                    │     │
│     │  - id (UUID)                                         │     │
│     │  - chat_id (FK)                                      │     │
│     │  - type (resume_pdf, resume_tex, cover_letter_pdf)   │     │
│     │  - minio_path (VARCHAR)                              │     │
│     │  - created_at                                        │     │
│     └──────────────────────────────────────────────────────┘     │
│                                                                  │
│  4. Download:                                                    │
│     ┌──────────────────────────────────────────────────────┐     │
│     │  GET /api/v1/artifacts/{id}/download                 │     │
│     │  Returns: 302 redirect to presigned MinIO URL        │     │
│     │         or 200 with file bytes (direct download)    │     │
│     └──────────────────────────────────────────────────────┘     │
│                                                                  │
│  5. Display in Chat:                                             │
│     ┌──────────────────────────────────────────────────────┐     │
│     │  Artifact Card:                                      │     │
│     │  ┌────────────────────────────────────────────┐      │     │
│     │  │  📄 resume.pdf                             │      │     │
│     │  │  24 KB  •  Generated 2 min ago             │      │     │
│     │  │  [Preview] [Download]                      │      │     │
│     │  └────────────────────────────────────────────┘      │     │
│     └──────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Error Handling Flow

> **Test coverage:** [Test Spec.md](Test%20Spec.md#16-security-tests) — error state tests in E2E.

### 5.1 LaTeX Compilation Error

```
┌──────────────────────────────────────────────────────────────────┐
│  AI:                                                             │
│  "Unfortunately, a LaTeX compilation error occurred."             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  🐛 LaTeX Compilation Error                                │  │
│  │  ┌────────────────────────────────────────────────────┐    │  │
│  │  │  ! Package amsmath Error: The environment `align'  │    │  │
│  │  │  requires "amsmath" package.                       │    │  │
│  │  └────────────────────────────────────────────────────┘    │  │
│  │  ┌────────────────────────────────────────────────────┐    │  │
│  │  │  [Retry Compilation]  [View Full Log]              │    │  │
│  │  └────────────────────────────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 LLM API Error

```
┌──────────────────────────────────────────────────────────────────┐
│  AI:                                                             │
│  "Failed to get response from LLM."                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  ⚠  LLM API Error: Rate limit exceeded                     │  │
│  │  ┌────────────────────────────────────────────────────┐    │  │
│  │  │  [Retry]  [Switch Model]  [Use Offline Mode]       │    │  │
│  │  └────────────────────────────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Streaming Visualization

### 6.1 Thinking Status

```
┌──────────────────────────────────────────────────────────────────┐
│  🧠 Thinking...                                                  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  ⏱ 00:03  │  📊 1.2k tokens  │  🔵 [Parsing Vacancy]       │  │
│  └────────────────────────────────────────────────────────────┘  │
│  Steps:                                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  ✓ Parsing Vacancy   (00:01)                               │  │
│  │  ✓ Selecting Context   (00:02)                             │  │
│  │  ● Formulating Questions   (current, 00:03)                │  │
│  │  ○ Generating TeX                                          │  │
│  │  ○ Compiling PDF                                           │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Token Usage Display

- **Prompt tokens** — tokens sent to LLM (vacancy + knowledge files + template + prompt).
- **Completion tokens** — tokens generated by LLM.
- Displayed in real-time during streaming.
- Saved to DB in the `messages` table (JSONB: `token_usage: {prompt_tokens, completion_tokens}`).

---

## 7. Cover Letter Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  User: "Generate Cover Letter"                                   │
│                                                                  │
│  AI (Streaming):                                                 │
│  ⏱ 00:02  │  📊 800 tokens  │  [Generating Cover Letter]...      │
│                                                                  │
│  AI: "Done!" + 📎 Artifact:                                      │
│      ┌────────────────────────────────────────────────────┐      │
│      │  📄 cover_letter_python_backend_yandex.pdf         │      │
│      │  [Download PDF]  [Download TeX]                    │      │
│      └────────────────────────────────────────────────────┘      │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  [Compare with Resume]                                     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. Settings Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  Settings                                                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  LLM Configuration                                         │  │
│  │  ┌────────────────────────────────────────────────────┐    │  │
│  │  │  Provider:  [OpenAI ▼]                             │    │  │
│  │  │  Host:      [https://api.openai.com]               │    │  │
│  │  │  API Key:   [••••••••••••••••••••••••••••••]       │    │  │
│  │  │  [Set as Default]                                  │    │  │
│  │  └────────────────────────────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Environment Variables                                     │  │
│  │  MAX_KNOWLEDGE_FILES:  [10]                                │  │
│  │  MAX_KNOWLEDGE_FILE_LENGTH:  [10000]                       │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 9. Summary: Flow States

| State | Description | Entry | Exit |
|-------|-------------|-------|------|
| **Empty** | Chat without messages | New Chat / Dashboard | User sends message |
| **Parsing** | Agent parses vacancy | User sends vacancy | Vacancy parsed |
| **Questioning** | Agent asks questions | Context insufficient | User answers |
| **Generating** | TeX generation | All data collected | TeX generated |
| **Compiling** | PDF compilation | TeX ready | PDF created |
| **Published** | Artifact created | Compilation done | User downloads |
| **Error** | Error at any stage | Any error | Retry / Switch model |

---

*Flow Spec v1.0 — Created 2026-08-04, based on Master Document §4, ADR-002, ADR-004, ADR-005, and User Stories.*
