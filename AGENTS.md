# 📋 Spec Driven Development

This project follows **Spec Driven Development** — requirements and architecture dictate the code, not vice versa. Before writing any implementation, always check the spec documents first.

---

## 📁 Repository Structure

```
Vacancy-Search/
├── docs/
│   ├── Master Document.md       ← Master Design Document (single source of truth)
│   ├── Design Spec.md           ← Architecture, modules, contracts, data, integrations
│   ├── API Contract.md          ← Detailed REST API & SSE contracts (endpoints, schemas, errors)
│   ├── Data Models.md           ← Domain data models, schemas, relationships
│   ├── Product Brief.md         ← Problem, solution, non-goals
│   ├── Flow Spec.md             ← User flows, states, interactions
│   ├── Test Spec.md             ← Test strategy (backend + frontend)
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
- API Contract Specification (REST + SSE) — [Master Document §7](docs/Master%20Document.md#7-api-contract-spec-rest--sse) (summary), [API Contract.md](docs/API%20Contract.md) (detailed)
- Security, Observability, Test Specifications
- Prompt Engineering Specification
- Task Breakdown & Implementation Plan

**Rule:** Never write code without checking the Master Document first. Requirements and architecture dictate the code.

---

## 🔄 Flow Specification

Located in `docs/Flow Spec.md` — detailed description of user flows, screen layouts, state transitions, and interactions.

Covers: authentication, onboarding, knowledge base, chat, streaming, artifacts, error handling, and settings.

---

## 📡 API Contract

Located in `docs/API Contract.md` — complete REST API and SSE contracts.

**Use API Contract when:**
- Defining new API endpoints (REST/SSE)
- Implementing request/response validation
- Documenting error codes and formats
- Designing SSE event handlers
- Reviewing auth requirements per endpoint

Covers: Authentication (OAuth, JWT, refresh), Users & LLM Configs, Knowledge Files, Chats (phases, messages, streaming), Artifacts (types, download), Admin endpoints, SSE event types and workflow, error format and codes, security mechanisms.

---

## 🏗️ Design Spec

Located in `docs/Design Spec.md` — comprehensive specification of architecture, modules, contracts, data, and integrations.

**Use Design Spec when:**
- Designing module boundaries or layer dependencies
- Defining new API endpoints (REST/SSE)
- Adding new entities, repositories, or use cases
- Planning integration with external services (OAuth, LLM providers, MinIO)
- Deciding on data storage strategy (PostgreSQL vs MinIO paths)
- Reviewing agent workflow and state transitions

Covers: Clean Architecture layers (Domain, Application, Infrastructure, Presentation), 6 LangGraph agent nodes, REST API contracts (summary), SSE event protocol, 12 entities, state machines, MinIO buckets, indexing strategy, and integration flows.

---

## 🗄️ Data Models

Located in `docs/Data Models.md` — complete domain data models for the system.

Covers: 9 core entities (`User`, `LLMConfig`, `KnowledgeFile`, `LatexTemplate`, `Chat`, `Message`, `Vacancy`, `Artifact`, `GlobalPrompt`), 3 extended entities (`AgentMessage`, `AuditLog`, `UserSettings`), state machines, ERD, SQL schema, indexing strategy, and design decisions.

---

## 🧪 Test Spec

Located in `docs/Test Spec.md` — comprehensive test strategy for backend and frontend.

**Use Test Spec when:**

- **Writing backend tests** — choose Unit (mocked infra, `pytest`), Integration (real Postgres/MinIO via `testcontainers`), or E2E (Playwright) based on what you're verifying
- **Writing frontend tests** — Component tests (Vitest + RTL), Hooks tests, Service layer (MSW), or E2E (Playwright)
- **Testing the agent** — mock LLM responses to verify LangGraph node transitions and SSE event sequences
- **Setting up CI/CD** — use the test commands and GitHub Actions example
- **Deciding what to mock** — `IUserRepository`, `IMinioStorage`, `ILLMProvider`, `ILatexCompiler` are the 4 interfaces to mock for Use Case tests
- **Adding a new entity** — write unit tests for domain invariants first, then integration for repository CRUD

**Key rules for testing:**

- Test Use Case **behavior**, not implementation internals
- Use real test doubles (not `MagicMock`) for domain interfaces
- Integration tests run in isolated containers — no shared state
- Agent tests inject `MockLLMClient` with deterministic responses
- Frontend hooks test event sequences, not just component rendering
- Coverage target: ≥80% for components/hooks, ≥75% overall

**Quick reference:**

- Backend test structure: `backend/tests/unit/`, `backend/tests/integration/`, `backend/tests/e2e/`
- Frontend test structure: `frontend/src/tests/unit/`, `frontend/src/tests/integration/`, `frontend/src/tests/e2e/`
- Mark tests with `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e` for selective runs

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
2. **Check Design Spec** — Review `docs/Design Spec.md` for architecture, modules, and contracts
3. **Check ADRs** — Look at `docs/adr/` for architectural decisions
4. **Check Data Models** — Review `docs/Data Models.md` for entity definitions, schemas, and relationships
5. **Check Epics** — Find the relevant Epic in `docs/epics/`
6. **Check Flow Spec** — Review `docs/Flow Spec.md` for UI/UX details
7. **Implement** — Write code following Clean Architecture
8. **Test** — Unit → Integration → E2E
9. **Update Docs** — Update OpenAPI, add/update ADRs if needed

### Key Rules

- NEVER import `infrastructure` or `presentation` into `domain` or `application`
- Design Spec defines module boundaries and layer dependencies — follow them
- NEVER execute LaTeX compilation directly — ALWAYS use `PodmanLatexCompiler`
- NEVER store file contents in PostgreSQL — store MinIO paths
- NEVER hardcode LLM prompts — fetch from `global_prompts`
- Domain models must match the definitions in `docs/Data Models.md`
- Use `podman-compose` for local development (`make dev`)
- All streaming uses SSE events with the defined format
- New ADRs reference Design Spec when changing architecture or adding modules

---

*Spec Driven Development, 2026-08-07*
