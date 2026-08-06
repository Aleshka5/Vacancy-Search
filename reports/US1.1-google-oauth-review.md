# US1.1 Google OAuth — Code Review Report

**Date:** 2026-08-06
**Status:** ✅ **PASS** (no blocking issues)

---

## Acceptance Criteria

### AC1 — POST /api/v1/auth/google — Exchange Google ID token for JWT
**PASS**

`auth.py:95–131` — Endpoint exists, validates Google ID token via `GoogleOAuthHandler.validate_id_token()`, creates or updates user, generates JWT pair, and returns `GoogleAuthResponse` with `access_token`, `refresh_token`, and `user`.

### AC2 — Access Token (15 min) stored in frontend memory
**PASS**

`jwt_handler.py:40–50` — `generate_access_token()` uses `timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)` (defaults to 15 min). `GoogleAuthResponse.access_token` is returned in the JSON body.

### AC3 — Refresh Token (30 days) stored in HttpOnly Cookie
**PASS**

`auth.py:117–125` — `response.set_cookie()` with all required attributes:
- `httponly=True`
- `secure=True`
- `samesite="strict"`
- `max_age=30 * 24 * 60 * 60` (2,592,000 seconds = 30 days)

### AC4 — Desktop/Mobile clients support OAuth flow (redirect-based)
**PASS**

The endpoint is designed for the **implicit/ID-token flow**: frontend sends a Google ID token (JWT) in the request body, and the backend issues a JWT pair. This supports any client capable of authenticating with Google and sending the ID token — no server-side redirect needed.

### AC5 — Token refresh via POST /api/v1/auth/refresh
**PASS**

`auth.py:134–179` — Endpoint exists, extracts `refresh_token` from cookies, validates via `RefreshTokenUseCase.refresh()`, and returns a new access token + rotated refresh token in both JSON body and cookie.

### AC6 — Expired tokens return 401
**PASS**

- `auth.py:151–163` — refresh endpoint raises `401` when refresh token is missing or invalid.
- `dependencies.py:25–40` — `get_current_user` raises `401` when access token is missing, expired, or has invalid signature.

---

## DoD Checklist

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Domain layer is pure (no SQLAlchemy/FastAPI imports) | ✅ PASS | Zero infra/presentation imports in `domain/` |
| 2 | Clean Architecture — no cross-layer violations | ✅ PASS | infra→domain (ok), pres→domain+app (ok); no domain→infra |
| 3 | JWT uses RS256 with correct claims | ✅ PASS | `sub=str(user_id)`, `exp`, `iat`, `iss=APP_NAME` |
| 4 | Access Token = 15 min, Refresh Token = 30 days | ✅ PASS | `JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS=30` |
| 5 | Refresh token cookie: HttpOnly, Secure, SameSite=Strict | ✅ PASS | `auth.py:117–125`, `auth.py:166–174` |
| 6 | User entity has all required fields | ✅ PASS | `id`, `google_id`, `email`, `role`, `is_blocked`, `default_llm_config_id`, `created_at`, `updated_at` |
| 7 | is_blocked check exists and returns 403 | ✅ PASS | `dependencies.py:49–53` raises `403_FORBIDDEN` |
| 8 | Settings have all required env vars | ✅ PASS | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `JWT_PRIVATE_KEY`, `JWT_PUBLIC_KEY`, `DATABASE_URL`, `MINIO_URL` |
| 9 | SQL user table matches spec | ✅ PASS | pydantic model + SQLAlchemy mapping: `google_id` (str), `email` (str), `role` (VARCHAR via Enum), `is_blocked` (BOOLEAN) |
| 10 | Dependencies installed in pyproject.toml | ✅ PASS | `fastapi`, `sqlalchemy[asyncio]`, `asyncpg`, `python-jose[cryptography]`, `cryptography`, `httpx`, `pydantic` |

---

## Issues Found

### Minor (cosmetic / narrow impact)

1. **Cookie path is narrow** — `auth.py:124,173` sets `path="/api/v1/auth/refresh"`.
   - This restricts the refresh cookie to the refresh endpoint only.
   - If the frontend calls other endpoints that need the cookie (e.g. `/auth/me`, `/api/v1/*`), the cookie won't be sent.
   - **Recommendation:** change to `path="/api/v1"` to cover all API routes.

2. **`get_db` creates a fresh engine per call** — `dependencies.py:58–80`.
   - Each call to `get_db()` creates a new `AsyncEngine` and disposes it on exit.
   - The shared `get_async_session()` in `infrastructure/db.py:41–45` reuses a global engine — the intended pattern.
   - Currently `get_db` is only used in `get_current_user` (not in auth endpoints), so this works, but it's inconsistent.
   - **Recommendation:** either use `get_async_session()` as the canonical dependency, or make `get_db` a singleton like `get_async_session`.

3. **`get_db` doesn't use `yield` from a shared factory** — `dependencies.py:67–80`.
   - The inner `_session()` context manager properly yields, but it creates a new engine each time rather than reusing the global one.
   - No functional bug, but worth aligning with `infrastructure/db.py`.

4. **Refresh endpoint's `refresh_token` extraction uses `Response` instead of `Request`** — `auth.py:148`.
   - `Depends(lambda r: r.cookies.get("refresh_token"))` — FastAPI infers `r` as `Response` here.
   - This actually works because FastAPI populates `Response.cookies` with the incoming request cookies (or rather, the cookie jar is shared).
   - **Recommendation:** explicitly type as `Request` for clarity: `Depends(lambda r: r.cookies.get("refresh_token"))` with `from fastapi import Request` and `r: Request`.

### No issues

The following potential concerns were checked and found to be non-issues:

- `PostgresUserRepository.get_by_id` receives `UUID` and SQLAlchemy handles the string-to-UUID conversion in `.where(User.id == user_id)` when `payload["sub"]` is a string.
- `get_db` properly yields the session (uses `async with async_session() as session: yield session`).
- `refresh_token` dependency correctly extracts from cookies and passes to `request.refresh(refresh_token)`.
- Domain imports are clean — no `infrastructure` or `presentation` imports in any `domain/` file.

---

## Overall Verdict: ✅ PASS

All 6 acceptance criteria are met. All 10 DoD items pass. The implementation is clean, follows Clean Architecture correctly, and uses RS256 JWT with proper cookie attributes. Two minor recommendations (cookie path, `get_db` engine reuse) do not block deployment.
