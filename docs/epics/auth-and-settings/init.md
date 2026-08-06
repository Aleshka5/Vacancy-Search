# Epic 1: Auth & Settings

## Overview
User authentication, session management, LLM configuration, and admin capabilities.

## Story Count
3 stories

## Stories

| # | Title | Story | Status |
|---|-------|-------|--------|
| US1.1 | Google OAuth Login | [View](us1.1.md) | ✅ Done |
| US1.2 | LLM Configuration | [View](us1.2.md) | Proposed |
| US1.3 | Admin User Blocking | [View](us1.3.md) | Proposed |

## Dependencies
- **Infrastructure:** PostgreSQL, MinIO (for storing encrypted API keys)
- **ADR:** ADR-006 (Containerization), ADR-003 (Blob Storage)

## Implementation Priority
1. US1.1 — Google OAuth (core auth)
2. US1.2 — LLM Configuration (user settings)
3. US1.3 — Admin User Blocking (admin feature)

## Implementation Plan
| Phase | Tasks |
|-------|-------|
| Phase 2.1 | Google OAuth 2.0 flow, Google Cloud console setup |
| Phase 2.2 | JWT (Access + Refresh tokens), HTTP-only cookie setup |
| Phase 2.3 | LLM Config model, encryption (Fernet/AES), UI settings |
| Phase 2.4 | Admin block middleware, Admin UI |

## Definition of Done (DoD)
- [ ] All stories implemented and merged
- [ ] Unit tests for Application layer (Use Cases)
- [ ] Integration tests for Infrastructure (Postgres, MinIO)
- [ ] Auth endpoints covered by E2E tests (Playwright)
- [ ] JWT tokens expire correctly (15 min access, 30 day refresh)
- [ ] LLM API keys are encrypted in database (AES/Fernet)
- [ ] Admin blocking works (403 on blocked user requests)
- [ ] Desktop and Mobile clients support OAuth flow
- [ ] Documentation updated (API docs, user guide)

---

*Epic generated from Master Document §3, 2026-08-04*
