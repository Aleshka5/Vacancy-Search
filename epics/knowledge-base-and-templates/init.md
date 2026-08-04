# Epic 2: Knowledge Base & Templates

## Overview
User's Markdown knowledge files and LaTeX templates — stored in MinIO, managed in the frontend, consumed by the LangGraph agent.

## Story Count
2 stories

## Stories

| ID | Title | Story | Status |
|----|-------|-------|--------|
| US2.1 | Upload Knowledge Files | [View](us2.1.md) | Proposed |
| US2.2 | Upload LaTeX Templates | [View](us2.2.md) | Proposed |

## Dependencies
- **Infrastructure:** MinIO (blob storage), PostgreSQL (metadata)
- **ADR:** ADR-003 (Blob Storage), ADR-005 (Agent Skills & Knowledge)
- **Epics:** Depends on Epic 1 (Auth) — users need to be authenticated

## Implementation Priority
1. US2.1 — Knowledge Files (core content)
2. US2.2 — LaTeX Templates (styling)

## Implementation Plan
| Phase | Tasks |
|-------|-------|
| Phase 3.1 | MinIO integration, upload endpoint, multipart handling |
| Phase 3.2 | Knowledge File model, description field, list endpoint |
| Phase 3.3 | LaTeX Template model, upload endpoint |
| Phase 3.4 | Frontend UI for file management |

## Definition of Done (DoD)
- [ ] All stories implemented and merged
- [ ] Unit tests for Application layer (Use Cases)
- [ ] Integration tests for MinIO storage
- [ ] File upload with size/quantity limits enforced
- [ ] Knowledge files have descriptions (used by Agent for skill selection)
- [ ] LaTeX templates saved as-is (no transformation)
- [ ] Frontend UI for file management
- [ ] Error handling: invalid files, size limits, MinIO errors
- [ ] Documentation updated

---

*Epic generated from Master Document §3, 2026-08-04*
