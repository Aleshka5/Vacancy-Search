# Epic 3: Chat & Agent

## Overview
The core of the application: Chat interface, LangGraph agent processing, and PDF generation.

## Story Count
4 stories

## Stories

| ID | Title | Story | Status |
|----|-------|-------|--------|
| US3.1 | Send Vacancy Text | [View](us3.1.md) | Proposed |
| US3.2 | Agent Questions | [View](us3.2.md) | Proposed |
| US3.3 | Agent Thinking Process | [View](us3.3.md) | Proposed |
| US3.4 | Cover Letter Generation | [View](us3.4.md) | Proposed |

## Dependencies
- **Infrastructure:** PostgreSQL, MinIO, Podman Sandbox
- **ADR:** ADR-002 (SSE), ADR-004 (LaTeX Sandbox), ADR-005 (Agent Skills & Knowledge)
- **Epics:** Depends on Epic 1 (Auth), Epic 2 (Knowledge Base)

## Implementation Priority
1. US3.1 — Send Vacancy Text (core chat)
2. US3.3 — Agent Thinking Process (streaming)
3. US3.2 — Agent Questions (interactive)
4. US3.4 — Cover Letter Generation (feature)

## Implementation Plan
| Phase | Tasks |
|-------|-------|
| Phase 5.1 | Chat model, messages model, chat endpoints |
| Phase 5.2 | Vacancy Parser node, JSON extraction |
| Phase 5.3 | Context Retriever, Questioner nodes |
| Phase 5.4 | SSE streaming endpoint, status events |
| Phase 5.5 | Cover Letter entity, generation flow |

## Definition of Done (DoD)
- [ ] All stories implemented and merged
- [ ] Unit tests for Application layer (Use Cases)
- [ ] Agent tests with mocked LLM provider
- [ ] Integration tests: Chat, Messages, Artifacts
- [ ] E2E tests: Playwright for UI chat flow
- [ ] SSE events follow the defined format
- [ ] Agent thinking process visible in UI
- [ ] Cover Letter generation works end-to-end
- [ ] Error handling: LaTeX compilation, LLM API errors
- [ ] Documentation updated (API docs, agent flow)

---

*Epic generated from Master Document §3, 2026-08-04*
