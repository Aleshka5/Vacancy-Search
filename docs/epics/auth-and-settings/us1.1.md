# US1.1: Google OAuth Login

## Status
**✅ Done**

## Story
**As a** user, I want to log in through Google OAuth, so that I don't need to remember another password.

## Acceptance Criteria

- [x] **AC1:** User can initiate Google OAuth login from the frontend
- [x] **AC2:** Access Token (15 min) stored in frontend memory
- [x] **AC3:** Refresh Token (30 days) stored in HttpOnly Cookie
- [x] **AC4:** Desktop/Mobile clients support OAuth flow (redirect-based)
- [x] **AC5:** Token refresh happens automatically before Access Token expiry
- [x] **AC6:** Expired tokens return 401 and trigger re-auth

## Technical Details

### Backend
- `POST /api/v1/auth/google` — Exchange Google code for JWT
- `POST /api/v1/auth/refresh` — Refresh access token using refresh cookie
- JWT format: RS256, with `sub` (user_id), `exp`, `iat`, `iss` claims

### Frontend
- Store Access Token in memory (not localStorage)
- Refresh Token in HttpOnly, Secure, SameSite=Strict cookie
- Auto-refresh interceptor on Axios/fetch

### Data Model
```sql
-- users table (from Master Document §5)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    google_id VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    role VARCHAR DEFAULT 'USER',
    is_blocked BOOLEAN DEFAULT FALSE,
    default_llm_id UUID,
    created_at TIMESTAMP
);
```

## References
- [Master Document §3 — US1.1](../../docs/Master%20Document.md#us11)
- [Master Document §8 — Security Spec](../../docs/Master%20Document.md#8-security-spec)
- [ADR-006 — Containerization](../../adr/006-containerization.md)
- [ADR-003 — Blob Storage](../../adr/003-blob-storage.md)

## Definition of Done (DoD)
- [x] Google OAuth flow works end-to-end (frontend → backend → Google → redirect)
- [x] Access Token expires after 15 minutes
- [x] Refresh Token persists for 30 days
- [x] Token refresh works automatically
- [x] Desktop/Mobile redirect flow tested
- [x] Unit tests: JWT generation, token validation
- [x] Integration tests: OAuth endpoint with testcontainers
- [x] E2E test: Playwright flow from login to dashboard
- [x] Security: tokens use RS256, refresh token is HttpOnly + Secure + SameSite=Strict

---

*US generated from Master Document §3, 2026-08-04*
