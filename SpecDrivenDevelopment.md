# 📋 Spec Driven Development

This project follows **Spec Driven Development** — requirements and architecture dictate the code, not vice versa. Before writing any implementation, always check the spec documents first.

---

## 📁 Repository Structure

```
Vacancy-Search/
├── docs/
│   ├── Master Document.md       ← Master Design Document (single source of truth)
│   ├── Design Spec.md           ← Architecture, modules, contracts, data, integrations
│   ├── Data Models.md           ← Domain data models, schemas, relationships
│   ├── Product Brief.md         ← Problem, solution, non-goals
│   ├── Flow Spec.md             ← User flows, states, interactions
│   ├── adr/                     ← Architectural Decision Records
│   │   ├── index.md             ← Index of all ADRs
│   │   └── adr-template.md      ← Template for new ADRs
│   └── epics/                   ← Epics and User Stories
│       ├── init.md              ← Epic index
│       └── <epic-name>/         ← Epic folders
│           └── init.md          ← Epic overview, DoD
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
- Data Model Specification (PostgreSQL) — basic schema in Master Document
- Data Models.md — full domain models, relationships, state machines, SQL
- Design Specification (Clean Architecture layers)
- API Contract Specification (REST + SSE)
- Security, Observability, Test Specifications
- Prompt Engineering Specification
- Task Breakdown & Implementation Plan

**Rule:** Never write code without checking the Master Document first. Requirements and architecture dictate the code.

---

## 🔄 Flow Specification

Located in `docs/Flow Spec.md` — detailed description of user flows, screen layouts, state transitions, and interactions.

Covers: authentication, onboarding, knowledge base, chat, streaming, artifacts, error handling, and settings.

---

## 🗄️ Data Models

Located in `docs/Data Models.md` — complete domain data models for the system.

Covers: 9 core entities (`User`, `LLMConfig`, `KnowledgeFile`, `LatexTemplate`, `Chat`, `Message`, `Vacancy`, `Artifact`, `GlobalPrompt`), 3 extended entities (`AgentMessage`, `AuditLog`, `UserSettings`), state machines, ERD, SQL schema, indexing strategy, and design decisions.

---

## 🏗️ Architectural Decision Records (ADR)

Located in `docs/adr/` — each ADR follows standard format (Status, Context, Decision, Consequences).

Key ADRs:
- **ADR-001**: Clean Architecture (no DDD)
- **ADR-002**: SSE for streaming
- **ADR-003**: MinIO for blobs, Postgres for metadata
- **ADR-004**: Podman sandbox for LaTeX
- **ADR-005**: Agent Skills & Knowledge
- **ADR-006**: Containerization with Podman

See `docs/adr/index.md` for full list. New ADRs use `adr-template.md`.

---

## 🎯 Epics & User Stories

Located in `docs/epics/` — organized hierarchically with init files for overviews.

Each Epic folder contains:
1. **init.md** — overview, dependencies, DoD
2. **us{X}.{Y}.md** — individual user stories with AC, technical details

Key Epics:
- **Epics 1**: Auth & Settings — Google OAuth, LLM config, Admin blocking
- **Epics 2**: Knowledge Base & Templates — MD files, LaTeX templates
- **Epics 3**: Chat & Agent — Vacancy parsing, Agent questions, Streaming, Cover Letters

See `docs/epics/init.md` for full index.

---

## 🔄 Development Workflow

1. **Read the Spec** — Locate the relevant section in `docs/Master Document.md`
2. **Check ADRs** — Look at `docs/adr/` for architectural decisions
3. **Check Data Models** — Review `docs/Data Models.md` for entity definitions, schemas, and relationships
4. **Check Epics** — Find the relevant Epic in `docs/epics/`
5. **Check Flow Spec** — Review `docs/Flow Spec.md` for UI/UX details
6. **Implement** — Write code following Clean Architecture
7. **Test** — Unit → Integration → E2E
8. **Update Docs** — Update OpenAPI, add/update ADRs if needed

### Key Rules

- NEVER import `infrastructure` or `presentation` into `domain` or `application`
- NEVER execute LaTeX compilation directly — ALWAYS use `PodmanLatexCompiler`
- NEVER store file contents in PostgreSQL — store MinIO paths
- NEVER hardcode LLM prompts — fetch from `global_prompts`
- Domain models must match the definitions in `docs/Data Models.md`
- Use `podman-compose` for local development (`make dev`)
- All streaming uses SSE events with the defined format

---

*Spec Driven Development, 2026-08-04*
