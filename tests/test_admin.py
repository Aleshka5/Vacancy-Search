"""Tests for admin endpoints (US 1.3: Admin User Blocking)."""

import pytest
from httpx import ASGITransport, AsyncClient
from uuid import uuid4

from backend.config.settings import Settings
from backend.domain.entities.user import User
from backend.domain.value_objects.role import Role
from backend.infrastructure.auth.jwt_handler import JWTHandler
from backend.infrastructure.repositories.fake_user_repository import FakeUserRepository
from backend.presentation.dependencies import get_current_user, get_current_admin

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def fake_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
async def admin_user(fake_repo) -> User:
    admin = User(
        id=uuid4(),
        google_id="admin-1",
        email="admin@test.com",
        role=Role.ADMIN,
        is_blocked=False,
    )
    await fake_repo.create(admin)
    return admin


@pytest.fixture
async def normal_user(fake_repo) -> User:
    user = User(
        id=uuid4(),
        google_id="user-1",
        email="user@test.com",
        role=Role.USER,
        is_blocked=False,
    )
    await fake_repo.create(user)
    return user


@pytest.fixture
async def blocked_user(fake_repo) -> User:
    user = User(
        id=uuid4(),
        google_id="blocked-1",
        email="blocked@test.com",
        role=Role.USER,
        is_blocked=True,
    )
    await fake_repo.create(user)
    return user


@pytest.fixture
async def blocked_admin(fake_repo) -> User:
    admin = User(
        id=uuid4(),
        google_id="blocked-admin-1",
        email="blocked-admin@test.com",
        role=Role.ADMIN,
        is_blocked=True,
    )
    await fake_repo.create(admin)
    return admin


# ------------------------------------------------------------------
# Test RSA keys — generate once and cache
# ------------------------------------------------------------------

_test_rsa_keys = None


def _get_test_rsa_keys():
    global _test_rsa_keys
    if _test_rsa_keys is not None:
        return _test_rsa_keys
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    _test_rsa_keys = (private_pem, public_pem)
    return _test_rsa_keys


def _make_test_settings():
    s = Settings()
    private_pem, public_pem = _get_test_rsa_keys()
    s.JWT_PRIVATE_KEY = private_pem
    s.JWT_PUBLIC_KEY = public_pem
    return s


def _make_token(user_id, settings=None):
    handler = JWTHandler(settings or _make_test_settings())
    return handler.generate_access_token(user_id)


# ------------------------------------------------------------------
# Helpers — patch dependency modules so get_current_user/admin work
# ------------------------------------------------------------------

@pytest.fixture(autouse=True)
def patched_deps(fake_repo):
    """Auto-patch all dependency lookups."""
    import backend.presentation.dependencies as deps
    import backend.presentation.routers.admin as admin_mod

    settings = _make_test_settings()
    deps._user_repo = fake_repo
    deps._jwt_handler = JWTHandler(settings)
    deps._settings = settings

    admin_mod._user_repo = fake_repo
    admin_mod._jwt_handler = JWTHandler(settings)
    admin_mod._settings = settings

    yield

    # Restore
    deps._user_repo = None
    deps._jwt_handler = None
    deps._settings = None
    admin_mod._user_repo = None
    admin_mod._jwt_handler = None
    admin_mod._settings = None


# ------------------------------------------------------------------
# Tests — get_current_user (normal endpoints)
# ------------------------------------------------------------------


class TestGetCurrentUser:
    """Blocked user gets 403 on normal endpoints; admin always gets through."""

    @pytest.mark.asyncio
    async def test_normal_user_authenticates(self, normal_user):
        user = await get_current_user()
        assert user == normal_user

    @pytest.mark.asyncio
    async def test_blocked_user_gets_403(self, blocked_user):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user()
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Account is blocked"

    @pytest.mark.asyncio
    async def test_blocked_admin_gets_through(self, blocked_admin):
        """Blocked admin should get through on normal endpoints."""
        user = await get_current_user()
        assert user == blocked_admin


# ------------------------------------------------------------------
# Tests — get_current_admin
# ------------------------------------------------------------------


class TestGetCurrentAdmin:
    """Admin dependency for admin endpoints."""

    @pytest.mark.asyncio
    async def test_admin_authenticates(self, admin_user):
        user = await get_current_admin()
        assert user.role == Role.ADMIN

    @pytest.mark.asyncio
    async def test_normal_user_gets_403(self, normal_user):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin()
        assert exc_info.value.status_code == 403
        assert "Admin access required" in str(exc_info.value.detail)


# ------------------------------------------------------------------
# Tests — Admin endpoints (via FastAPI app)
# ------------------------------------------------------------------


def _make_test_app(fake_repo, admin_user_id, admin_role, user_role=Role.USER):
    """Create a test FastAPI app with our admin router and injected deps."""
    from fastapi import FastAPI
    from backend.presentation.routers.admin import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    import backend.presentation.routers.admin as admin_mod

    settings = _make_test_settings()
    admin_mod._user_repo = fake_repo
    admin_mod._jwt_handler = JWTHandler(settings)
    admin_mod._settings = settings

    # Inject test admin user into the repo
    admin = User(
        id=admin_user_id,
        google_id=f"admin-{admin_user_id}",
        email="admin@test.com",
        role=admin_role,
        is_blocked=False,
    )
    fake_repo._store[admin.id] = admin

    return app


class TestAdminEndpoints:
    """Admin CRUD operations on users."""

    @pytest.mark.asyncio
    async def test_admin_can_list_users(self, fake_repo, admin_user, normal_user):
        """Admin can list all users (paginated)."""
        user3 = User(
            id=uuid4(),
            google_id="user-2",
            email="user2@test.com",
            role=Role.USER,
            is_blocked=False,
        )
        await fake_repo.create(user3)

        app = _make_test_app(fake_repo, admin_user.id, Role.ADMIN)
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            token = _make_token(admin_user.id)
            resp = await client.get(
                "/api/v1/admin/users",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["total"] == 4
            assert len(data["items"]) == 4
            assert data["page"] == 1
            assert data["per_page"] == 20

    @pytest.mark.asyncio
    async def test_admin_can_block_user(self, fake_repo, admin_user, normal_user):
        """Admin can block a user."""
        user_id = str(normal_user.id)
        app = _make_test_app(fake_repo, admin_user.id, Role.ADMIN)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            token = _make_token(admin_user.id)
            resp = await client.patch(
                f"/api/v1/admin/users/{user_id}/block",
                json={"blocked": True},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["is_blocked"] is True

    @pytest.mark.asyncio
    async def test_admin_can_unblock_user(self, fake_repo, admin_user, blocked_user):
        """Admin can unblock a user."""
        user_id = str(blocked_user.id)
        app = _make_test_app(fake_repo, admin_user.id, Role.ADMIN)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            token = _make_token(admin_user.id)
            resp = await client.patch(
                f"/api/v1/admin/users/{user_id}/unblock",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["is_blocked"] is False

    @pytest.mark.asyncio
    async def test_admin_can_toggle_block(self, fake_repo, admin_user, normal_user):
        """Admin can toggle block state."""
        user_id = str(normal_user.id)
        app = _make_test_app(fake_repo, admin_user.id, Role.ADMIN)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            token = _make_token(admin_user.id)
            # Toggle from unblocked -> blocked
            resp = await client.patch(
                f"/api/v1/admin/users/{user_id}/toggle-block",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["is_blocked"] is True

            # Toggle again -> unblocked
            resp = await client.patch(
                f"/api/v1/admin/users/{user_id}/toggle-block",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["is_blocked"] is False

    @pytest.mark.asyncio
    async def test_non_admin_gets_403(self, fake_repo, normal_user):
        """Non-admin gets 403 on admin endpoints."""
        user_id = str(normal_user.id)
        app = _make_test_app(fake_repo, normal_user.id, Role.USER)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            token = _make_token(normal_user.id)
            resp = await client.patch(
                f"/api/v1/admin/users/{user_id}/block",
                json={"blocked": True},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_block_themselves(self, fake_repo, admin_user):
        """Admin can block themselves."""
        user_id = str(admin_user.id)
        app = _make_test_app(fake_repo, admin_user.id, Role.ADMIN)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            token = _make_token(admin_user.id)
            resp = await client.patch(
                f"/api/v1/admin/users/{user_id}/block",
                json={"blocked": True},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["is_blocked"] is True

    @pytest.mark.asyncio
    async def test_admin_pagination_params(self, fake_repo, admin_user):
        """Admin can specify page and per_page params."""
        for i in range(5):
            user = User(
                id=uuid4(),
                google_id=f"page-user-{i}",
                email=f"page-user-{i}@test.com",
                role=Role.USER,
                is_blocked=False,
            )
            await fake_repo.create(user)

        app = _make_test_app(fake_repo, admin_user.id, Role.ADMIN)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            token = _make_token(admin_user.id)
            resp = await client.get(
                "/api/v1/admin/users?page=1&per_page=2",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["per_page"] == 2
            assert data["page"] == 1
            assert len(data["items"]) == 2
            assert data["total"] >= 5
