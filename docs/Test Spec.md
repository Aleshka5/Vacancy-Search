# 🧪 Test Specification — Vacancy-Search

> **Version:** 1.0.0
> **Date:** 2026-08-05
> **Source:** Master Document (§10), Design Spec (§8), ADR-001 through ADR-006
> **Status:** Accepted

---

## 0. Overview

This document defines the **test strategy** for Vacancy-Search: what to test, at which level, with which tools, and how to organize test code.

**Guiding principles:**

- Test the **behavior** of Use Cases, not the internals of Infrastructure.
- Infrastructure is tested with real Postgres and MinIO (via `testcontainers`).
- Agent logic is tested by mocking LLM responses.
- Frontend tests mirror the user flows in [Flow Spec.md](Flow%20Spec.md).
- Keep test dependencies minimal — no circular imports.
- Tests must be **deterministic** and **fast** (CI < 5 min target).

---

## 1. Backend Test Strategy

### 1.1 Test Pyramid

```
          ┌─────────────┐
          │   E2E       │  Playwright (UI flows, SSE)
          └──────┬──────┘
          ┌──────┴──────┐
          │ Integration  │  pytest + testcontainers (Postgres, MinIO)
          └──────┬──────┘
          ┌──────┴──────┐
          │   Unit       │  pytest (Use Cases, Domain, Interfaces)
          └─────────────┘
```

### 1.2 Unit Tests

**Purpose:** Verify business logic in isolation — Use Cases and Domain logic with mocked Infrastructure.

**Tools:** `pytest`, `pytest-asyncio`, `pytest-mock`

**Scope:**

| Layer | What to test | Mocking |
|-------|-------------|---------|
| **Domain** | Entity rules, Value Objects, Enums, state transitions | Nothing (pure Python) |
| **Application** | Use Case logic, orchestration, DTO mapping | Mock `IUserRepository`, `IMinioStorage`, `ILLMProvider`, `ILatexCompiler` |
| **Presentation** | Pydantic schemas validation, router dependencies | Mock JWT, FastAPI `TestClient` |

**Key rules:**

- Use Case tests verify **one behavior** per test function.
- Domain tests verify invariants (e.g., `Chat.phase` transitions are valid).
- Never mock `unittest.mock.MagicMock` for interfaces — define real test doubles.

**Example patterns:**

```python
# Use Case with mocked infrastructure
async def test_generate_resume_creates_artifact():
    mock_compiler = AsyncMock(spec=ILatexCompiler)
    mock_compiler.compile.return_value = "path/to/file.pdf"
    mock_minio = AsyncMock(spec=IMinioStorage)
    mock_minio.upload.return_value = "/artifacts/abc.pdf"

    uc = GenerateResumeUseCase(
        latex_compiler=mock_compiler,
        minio_storage=mock_minio,
        artifact_repo=MagicMock(),
    )
    result = await uc.execute(chat_id=uuid1(), template="default")
    
    assert result.type == ArtifactType.RESUME_PDF
    mock_minio.upload.assert_awaited_once()

# Domain invariant
def test_chat_phase_transitions():
    assert ChatPhase.PARSING.is_valid_target(ChatPhase.QUESTIONING)
    assert not ChatPhase.QUESTIONING.is_valid_target(ChatPhase.EMPTY)
```

### 1.3 Integration Tests

**Purpose:** Test real database, MinIO, and external service interactions.

**Tools:** `pytest`, `pytest-asyncio`, `testcontainers` (Postgres, MinIO), `pytest-faker`

**Scope:**

| Component | What to test |
|-----------|-------------|
| **Repositories** | CRUD operations, transactions, IDOR checks |
| **MinIO** | Upload, download, presigned URLs, path generation |
| **Auth** | JWT generation/validation, OAuth callback, blocked users |
| **Agent pipeline** | End-to-end vacancy parsing → artifact creation |

**Container fixtures:**

```python
@pytest.fixture
def postgres():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg.get_connection_url()

@pytest.fixture
def minio():
    with MinIOContainer("minio/minio:latest") as mc:
        yield mc.get_config()
```

**Example patterns:**

```python
@pytest.mark.integration
async def test_upload_knowledge_file_persists_to_minio_and_db(
    postgres, minio, user_factory,
):
    db = PostgresSession(postgres)
    storage = MinioClient(minio)
    
    file_id = await uc.upload(
        user_id=user.id,
        title="Experience",
        description="Work experience",
        content=b"Hello",
    )
    
    # DB record exists
    record = await db.query(KnowledgeFile).filter(...).one()
    assert record.title == "Experience"
    
    # MinIO object exists
    assert storage.exists(record.minio_path)

@pytest.mark.integration
async def test_idor_prevents_access_to_other_users_artifacts(
    postgres, minio, user_factory,
):
    user_a, user_b = await user_factory.create_pair()
    artifact = await create_artifact(user_a, chat_a)
    
    # user_b cannot download user_a's artifact
    with pytest.raises(ForbiddenError):
        await uc.download(artifact_id=artifact.id, user_id=user_b.id)
```

### 1.4 Agent Tests

**Purpose:** Verify LangGraph agent node transitions and state management.

**Tools:** `pytest`, `pytest-asyncio`, `llama-index` (mock LLM), `langgraph`

**Scope:**

| Test Type | What to test |
|-----------|-------------|
| **Node transitions** | VacancyParser → ContextRetriever → Questioner → Generator → Compiler → Publisher |
| **State updates** | `ChatPhase` transitions at each node |
| **SSE event sequence** | Correct events emitted in correct order |
| **Error recovery** | Retry on LLM timeout, LaTeX compilation error |
| **Mocked LLM** | Inject deterministic responses via `MockLLMClient` |

**Example patterns:**

```python
async def test_agent_workflow_complete():
    mock_llm = MockLLMClient(responses={
        "vacancy_parser": '{"company":"Yandex","stack":["Python","FastAPI"]}',
        "questioner": "What is your experience with FastAPI?",
        "generator": "\\documentclass{article}...",
    })
    
    state = AgentState(chat_id=uuid1(), vacancy_text="...")
    result = await LangGraphAgent.execute(state, llm=mock_llm)
    
    assert result.phase == ChatPhase.PUBLISHED
    assert result.artifact.type == ArtifactType.RESUME_PDF
    assert result.sse_events == [
        "step_started", "status", "assistant_delta",
        "assistant_message", "artifact_created", "done",
    ]

async def test_retry_on_latex_error():
    mock_compiler = AsyncMock(spec=ILatexCompiler)
    mock_compiler.compile.side_effect = [
        LatexError("Package amsmath not found"),
        "path/to/fix.pdf",
    ]
    
    result = await uc.generate_resume(latex_compiler=mock_compiler)
    assert result.retries == 1
```

### 1.5 Infrastructure Tests

**Purpose:** Verify external service clients and sandbox behavior.

**Tools:** `pytest`, `pytest-asyncio`, `pytest-mock`

| Module | What to test |
|--------|-------------|
| **Postgres repositories** | Async queries, session management, migration compatibility |
| **MinIO client** | Presigned URL generation, multipart upload, bucket management |
| **Podman compiler** | Container lifecycle, `--network=none`, error handling |
| **LLM providers** | OpenAI, Anthropic, Ollama API contracts, streaming |
| **Auth** | JWT encoding/decoding, Google OAuth flow, key encryption |

### 1.6 Security Tests

**Purpose:** Verify auth, IDOR, and sandbox isolation.

| Test | Tool |
|------|------|
| JWT validation (expired, invalid, RS256) | `pytest` |
| Blocked user receives 403 | `TestClient` |
| IDOR protection on all endpoints | `TestClient` |
| Podman sandbox isolation | `pytest` + `podman` CLI |
| LLM API key encryption/decryption | `pytest` |

---

## 2. Frontend Test Strategy

### 2.1 Test Pyramid

```
          ┌─────────────┐
          │   E2E       │  Playwright (SSE streaming, chat flow)
          └──────┬──────┘
          ┌──────┴──────┐
          │ Integration  │  Vitest + MSW (API mocking)
          └──────┬──────┘
          ┌──────┴──────┐
          │   Unit       │  Vitest + React Testing Library
          └─────────────┘
```

### 2.2 Unit Tests (Component)

**Purpose:** Test React components in isolation.

**Tools:** `vitest`, `@testing-library/react`, `@testing-library/user-event`

**Scope:**

| Component | What to test |
|-----------|-------------|
| **Chat** | Message rendering, SSE updates, error display |
| **Artifact Card** | Download, preview, type display |
| **Sidebar** | Chat list, new chat, collapse/expand |
| **Knowledge Base** | File list, upload progress, delete |
| **Settings** | LLM config form, validation, save |
| **Auth** | Login button, blocked state, avatar |

**Example patterns:**

```typescript
it("renders streaming message with delta updates", async () => {
  render(<Chat />);
  userEvent.click(screen.getByRole("button", { name: /New Chat/i }));
  await userEvent.type(screen.getByRole("textbox"), "Senior Python dev");
  
  // SSE events arrive
  expect(await screen.findByText(/Analyzing/i)).toBeInTheDocument();
  expect(screen.getByText(/Senior Python/i)).toBeInTheDocument();
});

it("shows error when SSE connection fails", async () => {
  render(<Chat error={new Error("Connection lost")} />);
  expect(screen.getByText(/Connection lost/i)).toBeInTheDocument();
});
```

### 2.3 Hooks Tests

**Purpose:** Test custom hooks with mocked providers.

**Tools:** `vitest`, `@testing-library/react-hooks`

| Hook | What to test |
|------|-------------|
| `useSSE` | Event parsing, delta accumulation, error handling |
| `useAuth` | Login/logout, token refresh, blocked state |
| `useChat` | Message list, phase transitions, artifact rendering |
| `useKnowledgeBase` | File upload, delete, list |

**Example patterns:**

```typescript
it("useSSE accumulates deltas and emits final message", async () => {
  const { result } = renderHook(() => useSSE(url));
  
  // Simulate SSE events
  fireEventSSE(result.current, { event: "assistant_delta", data: { content: "Hello " } });
  fireEventSSE(result.current, { event: "assistant_delta", data: { content: "World" } });
  fireEventSSE(result.current, { event: "done", data: { message_id: "abc" } });
  
  expect(result.current.message).toBe("Hello World");
});
```

### 2.4 Service Layer Tests

**Purpose:** Test API client functions with mocked fetch.

**Tools:** `vitest`, `msw` (Mock Service Worker)

| Service | What to test |
|---------|-------------|
| `apiClient` | Request/response interceptors, auth headers |
| `chatService` | Create, list, stream, messages |
| `knowledgeService` | Upload, list, delete files |
| `authService` | Login, refresh, logout |

**Example patterns:**

```typescript
describe("chatService.create", () => {
  it("returns chat object with ID", async () => {
    server.use(
      rest.post("/api/v1/chats", (req, res, ctx) => {
        return res(ctx.json({ id: "abc", title: null, phase: "parsing" }));
      })
    );
    
    const result = await chatService.create({ vacancy_text: "..." });
    expect(result.id).toBe("abc");
  });
});
```

### 2.5 E2E Tests

**Purpose:** Verify complete user flows in real browser.

**Tools:** `playwright`, `@playwright/test`

**Flows to test (from [Flow Spec.md](Flow%20Spec.md)):**

| Flow | What to verify |
|------|---------------|
| **Onboarding** | Login → LLM config → MD upload → LaTeX → Dashboard |
| **Chat creation** | Paste vacancy → streaming response → questions → answers |
| **Artifact generation** | Request resume → see artifact card → download PDF |
| **Cover letter** | Generate cover letter → see artifact → compare with resume |
| **Error handling** | LaTeX error → retry → success |
| **Knowledge base** | Upload MD → edit → delete |
| **Settings** | Change LLM config → apply to chat |
| **Auth** | Login with Google → navigate → logout → refresh |
| **Admin** | Block user → verify 403 |

**Example patterns:**

```typescript
test("complete chat flow with streaming", async ({ page }) => {
  await page.goto("/");
  await page.fill('[placeholder="Paste vacancy"]', vacancyText);
  await page.click('button[type="submit"]');
  
  // Wait for streaming to complete
  await page.waitForSelector('[data-testid="artifact-card"]');
  
  // Verify artifact exists
  expect(await page.locator('[data-testid="artifact-card"]').textContent())
    .toContain("Resume");
  
  // Download and verify
  await page.click('[data-testid="download-pdf"]');
  const download = await page.waitForEvent("download");
  expect(download.suggestedFilename).toContain(".pdf");
});
```

---

## 3. Test Organization

### 3.1 Backend Structure

```
backend/
├── tests/
│   ├── conftest.py                  # Shared fixtures (testcontainers, factories)
│   ├── unit/
│   │   ├── test_use_cases.py        # Use Case unit tests
│   │   ├── test_domain.py           # Domain entity rules
│   │   └── test_schemas.py          # Pydantic schema validation
│   ├── integration/
│   │   ├── test_repositories.py     # Postgres + MinIO integration
│   │   ├── test_auth.py             # JWT + OAuth integration
│   │   └── test_agent_pipeline.py   # Full agent flow
│   ├── e2e/
│   │   ├── test_chat.py             # Playwright chat flows
│   │   └── test_knowledge.py        # Playwright knowledge flows
│   └── fixtures/
│       ├── factories.py             # Test data factories
│       └── samples/                 # Sample MD files, LaTeX templates
├── pyproject.toml                   # pytest config
```

### 3.2 Frontend Structure

```
frontend/
├── src/
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── components/
│   │   │   │   ├── Chat.test.tsx
│   │   │   │   └── ArtifactCard.test.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useSSE.test.ts
│   │   │   │   └── useAuth.test.ts
│   │   │   └── services/
│   │   │       └── apiClient.test.ts
│   │   ├── integration/
│   │   │   └── chat.test.tsx        # Component + API mock
│   │   └── e2e/
│   │       ├── chat.spec.ts         # Playwright
│   │       └── onboarding.spec.ts
│   ├── setupTests.ts               # Vitest globals, MSW setup
│   └── msw/                         # Service Worker handlers
├── vitest.config.ts
└── playwright.config.ts
```

### 3.3 Shared Test Configuration

```toml
# backend/pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "unit: unit tests",
    "integration: integration tests (requires containers)",
    "e2e: end-to-end tests (requires browser)",
    "slow: tests that take > 5s",
]

# frontend/vitest.config.ts
export default defineConfig({
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["src/setupTests.ts"],
    coverage: {
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/**/*.test.ts", "src/**/*.test.tsx", "src/**/*.d.ts"],
    },
  },
});
```

---

## 4. Test Data Management

### 4.1 Factories

Use factories for generating test data (not manual dict creation):

```python
class UserFactory:
    @classmethod
    async def create(cls, *, email=None, role=Role.USER) -> User:
        ...

class ChatFactory:
    @classmethod
    async def create(cls, *, user=None, phase=ChatPhase.EMPTY) -> Chat:
        ...
```

### 4.2 Sample Files

Store sample files in `tests/fixtures/samples/`:

```
tests/fixtures/samples/
├── sample_resume.md
├── sample_cover_letter.md
├── sample_latex.tex
└── sample_vacancy.txt
```

### 4.3 Test Fixtures (Postgres/MinIO)

Use `testcontainers` for isolated integration test databases:

```python
@pytest.fixture(scope="module")
def postgres():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg.get_connection_url()
```

### 4.4 Cleanup

- **Unit tests:** No cleanup needed (in-memory mocks).
- **Integration tests:** Containers auto-clean after test module.
- **E2E tests:** Playwright handles browser cleanup.

---

## 5. CI/CD Integration

### 5.1 Test Commands

```bash
# Backend — all tests
uv run pytest
uv run pytest -m unit          # Unit only (fast)
uv run pytest -m integration   # Integration (requires containers)
uv run pytest -m e2e           # E2E (requires browser)

# Frontend
cd frontend && npx vitest run
cd frontend && npx playwright test

# Full CI
uv run pytest && cd frontend && npx vitest run && npx playwright test
```

### 5.2 GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v2
      - run: uv run pytest -m unit
      - run: uv run pytest -m integration
      - run: uv run pytest -m e2e

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd frontend && npx vitest run
      - run: cd frontend && npx playwright test
```

---

## 6. Coverage Targets

| Scope | Target |
|-------|--------|
| **Backend Unit** | ≥ 80% |
| **Backend Integration** | ≥ 75% |
| **Frontend Components** | ≥ 80% |
| **Frontend Hooks** | ≥ 90% |
| **Overall** | ≥ 70% |

---

## 7. Traceability to Requirements

| Requirement | Test | Type |
|-------------|------|------|
| US1.1 (OAuth) | `test_google_oauth_flow()` | Integration |
| US1.2 (LLM Config) | `test_create_llm_config()` | Unit |
| US1.3 (Admin block) | `test_blocked_user_403()` | Integration |
| US2.1 (MD Files) | `test_upload_knowledge_file()` | Integration |
| US2.2 (LaTeX Template) | `test_upload_latex_template()` | Integration |
| US3.1 (Vacancy Parsing) | `test_vacancy_parser_node()` | Agent |
| US3.2 (Questions) | `test_questioner_node()` | Agent |
| US3.3 (Streaming) | `test_sse_events_sequence()` | Agent + E2E |
| US3.4 (Cover Letter) | `test_cover_letter_generation()` | Integration |
| ADR-004 (Sandbox) | `test_latex_compilation_isolation()` | Infrastructure |

---

## 8. Cross-Reference

| Document | Reference |
|----------|-----------|
| [Master Document.md](Master%20Document.md) | §10 Test Spec, §13 Prompt Engineering |
| [Design Spec.md](Design%20Spec.md) | §8 Test Strategy, §9 Traceability Matrix |
| [Flow Spec.md](Flow%20Spec.md) | §9 Flow States (used for E2E flows) |
| [Data Models.md](Data%20Models.md) | Entity definitions (used in test data factories) |
| [API Contract.md](API%20Contract.md) | Request/response schemas (used for API tests) |

---

*Test Specification v1.0 — Created 2026-08-05*
