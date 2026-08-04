# 📋 Spec Driven Development

This project follows **Spec Driven Development** — requirements and architecture dictate the code, not vice versa. Before writing any implementation, always check the spec documents first.

---

## 📁 Repository Structure

```
Vacancy-Search/
├── docs/
│   ├── Master Document.md       ← Master Design Document (single source of truth)
│   └── Product Brief.md         ← Problem, solution, non-goals
├── adr/                         ← Architectural Decision Records
│   ├── index.md                 ← Index of all ADRs
│   ├── adr-template.md          ← Template for new ADRs
│   ├── 001-clean-architecture-vs-ddd.md
│   ├── 002-sse-vs-websocket.md
│   ├── 003-blob-storage.md
│   ├── 004-latex-sandbox.md
│   ├── 005-agent-skills-knowledge.md
│   └── 006-containerization.md
├── epics/                       ← Epics and User Stories
│   ├── init.md                  ← Epic index
│   ├── auth-and-settings/       ← Epic 1: Auth & Settings
│   │   ├── init.md              ← Epic overview, DoD
│   │   ├── us1.1.md             ← US1.1: Google OAuth Login
│   │   ├── us1.2.md             ← US1.2: LLM Configuration
│   │   └── us1.3.md             ← US1.3: Admin User Blocking
│   ├── knowledge-base-and-templates/  ← Epic 2
│   │   ├── init.md
│   │   ├── us2.1.md
│   │   └── us2.2.md
│   └── chat-and-agent/          ← Epic 3
│       ├── init.md
│       ├── us3.1.md
│       ├── us3.2.md
│       ├── us3.3.md
│       └── us3.4.md
├── backend/                     ← Implementation (generated from specs)
│   ├── domain/                  ← Pure domain logic
│   ├── application/             ← Use Cases
│   ├── infrastructure/          ← DB, MinIO, LangGraph, Podman
│   ├── presentation/            ← FastAPI, SSE, JWT
│   └── config/                  ← ENV, Settings
├── frontend/                    ← Vite + React + TypeScript
└── deployment/                  ← Podman-compose, Dockerfiles
```

---

## 📐 Master Document

Located in `docs/Master Document.md` — the **single source of truth** for the project. Contains:

- Product Brief & Vision
- Architectural Decision Records (ADR-001 through ADR-006)
- Requirements Spec (Epics & User Stories)
- UX / Flow Specification
- Data Model Specification (PostgreSQL)
- Design Specification (Clean Architecture layers)
- API Contract Specification (REST + SSE)
- Security, Observability, Test Specifications
- Prompt Engineering Specification
- Task Breakdown & Implementation Plan

**Rule:** Never write code without checking the Master Document first. Requirements and architecture dictate the code.

---

## 🏗️ Architectural Decision Records (ADR)

Located in `adr/` directory. Each ADR follows the standard format:

- **Status:** Proposed → Accepted → Deprecated → Superseded
- **Context:** What led to the decision
- **Decision:** The actual decision and rationale
- **Consequences:** What becomes easier/more difficult

### ADR List

| ADR | Title | Summary |
|-----|-------|---------|
| ADR-001 | Clean Architecture vs DDD | Strict Clean Architecture without DDD complexity |
| ADR-002 | SSE vs WebSocket | SSE for streaming agent responses |
| ADR-003 | Blob Storage with MinIO | MinIO for files, Postgres for metadata only |
| ADR-004 | LaTeX Sandbox with Podman | Isolated Podman containers for LaTeX compilation |
| ADR-005 | Agent Skills & Knowledge | Two-level approach: description-based + content retrieval |
| ADR-006 | Containerization with Podman | Podman + podman-compose, K8s-ready architecture |

New ADRs should use `adr/adr-template.md` as a template and be added to `adr/index.md`.

---

## 🎯 Epics & User Stories

Located in `epics/` directory, organized hierarchically:

- **`epics/init.md`** — Index of all Epics with links
- **`epics/<epic-name>/init.md`** — Epic overview, story count, DoD
- **`epics/<epic-name>/us{X}.{Y}.md`** — Individual User Stories

### Epic Structure

Each Epic folder contains:
1. **init.md** — Epic overview, dependencies, implementation priority, Definition of Done (DoD)
2. **us{X}.{Y}.md** — Individual User Stories with:
   - Story statement (As a... I want... so that...)
   - Acceptance Criteria (checklist)
   - Technical Details (API endpoints, data models, code snippets)
   - References (links to Master Document and ADRs)
   - Definition of Done (DoD)

### Epics

| Epic | Folder | Stories | Focus |
|------|--------|---------|-------|
| 1 | `auth-and-settings/` | 3 | Google OAuth, LLM config, Admin blocking |
| 2 | `knowledge-base-and-templates/` | 2 | Markdown files, LaTeX templates |
| 3 | `chat-and-agent/` | 4 | Vacancy parsing, Agent questions, Streaming, Cover Letters |

### Status Flow

```
Proposed → In Progress → Done
```

- **Proposed:** Story is defined, AC defined, not yet started
- **In Progress:** Implementation started
- **Done:** Code + tests merged, DoD met

---

## 🔄 Development Workflow

1. **Read the Spec** — Locate the relevant section in `docs/Master Document.md`
2. **Check ADRs** — Look at `adr/` for architectural decisions
3. **Check Epics** — Find the relevant Epic in `epics/` and read the User Story
4. **Implement** — Write code following Clean Architecture (domain → application → infrastructure → presentation)
5. **Test** — Unit tests (Application), Integration tests (Infrastructure), E2E tests (Playwright)
6. **Update Docs** — Update OpenAPI, add/update ADRs if needed

### Key Rules

- NEVER import `infrastructure` or `presentation` into `domain` or `application`
- NEVER execute LaTeX compilation directly — ALWAYS use `PodmanLatexCompiler`
- NEVER store file contents in PostgreSQL — store MinIO paths
- NEVER hardcode LLM prompts — fetch from `global_prompts`
- Use `podman-compose` for local development (`make dev`)
- All streaming uses SSE events with the defined format

---

*Spec Driven Development, 2026-08-04*
