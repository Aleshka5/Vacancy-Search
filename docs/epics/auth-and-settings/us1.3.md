# US1.3: Admin User Blocking

## Status
**Proposed**

## Story
**As an** Admin, I want to block/unblock users, so that I can prevent abuse or suspend accounts.

## Acceptance Criteria

- [ ] **AC1:** Admin has access to Admin UI
- [ ] **AC2:** Admin can view all users and their status
- [ ] **AC3:** Admin can block/unblock a user
- [ ] **AC4:** Blocked users receive 403 on any API request
- [ ] **AC5:** Blocked users cannot access any endpoint (not just specific ones)
- [ ] **AC6:** Blocking takes effect immediately (no cache delay)

## Technical Details

### Backend
- `GET /api/v1/admin/users` — Admin lists all users
- `PATCH /api/v1/admin/users/{id}/block` — Block user
- `PATCH /api/v1/admin/users/{id}/unblock` — Unblock user
- **Middleware:** `BlockMiddleware` checks `is_blocked` on every request
  - Returns 403 if `user.is_blocked == True`
  - Does NOT affect Admin requests (admins are never blocked)

### Middleware Implementation
```python
class BlockMiddleware:
    async def __call__(self, request, call_next):
        user = await get_current_user(request)
        if user.is_blocked and user.role != "ADMIN":
            return JSONResponse(status_code=403, content={"detail": "User is blocked"})
        return await call_next(request)
```

### Admin Role
- Users with `role = 'ADMIN'` in `users` table
- Admin role is checked AFTER blocking decision
- Admin can block/unblock themselves (useful for self-suspension)

## References
- [Master Document §3 — US1.3](../../docs/Master%20Document.md#us13)
- [Master Document §8 — Security Spec](../../docs/Master%20Document.md#8-security-spec)
- [ADR-001 — Clean Architecture](../../adr/001-clean-architecture-vs-ddd.md) (middleware in Presentation layer)

## Definition of Done (DoD)
- [ ] Admin UI shows user list with block/unblock buttons
- [ ] Blocked user gets 403 on any API request
- [ ] Admins are not affected by blocking
- [ ] Blocking is immediate (no Redis/cache)
- [ ] Unit tests: middleware logic, admin role checks
- [ ] Integration tests: block/unblock API endpoints
- [ ] E2E test: admin blocks user, user gets 403
- [ ] Admin UI is accessible (role-based access control)

---

*US generated from Master Document §3, 2026-08-04*
