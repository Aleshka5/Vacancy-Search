Ниже представлено **Единое Техническое Задание (Master Design Document)**, объединяющее все запрошенные спецификации в рамках методологии Spec Driven Development. В конце документа расположены инструкции для LLM-исполнителей.

---

# 📚 MASTER DESIGN DOCUMENT: AI Resume & Cover Letter Generator

## 1. Product Brief / Vision

**Проблема:** Соискатели тратят часы на адаптацию резюме и написание сопроводительных писем под каждую конкретную вакансию, часто упуская ключевые требования.
**Решение:** AI-сервис, который хранит "базу знаний" пользователя (MD-файлы), анализирует текст вакансии, задает уточняющие вопросы и генерирует идеально сверстанные PDF (Resume/Cover Letter) через компиляцию LaTeX.
**Целевая аудитория:** IT-специалисты, менеджеры, академические работники.
**Non-goals (Что НЕ делаем):**

- Не делаем Job Board (доску объявлений).
- Не делаем ATS (Applicant Tracking System) интеграции и автоотклики.
- Не поддерживаем загрузку вакансий файлами (только текст).
- Не реализуем GDPR-экспорт и удаление аккаунта (на данном этапе).



## 2. Architectural Decision Records (ADRs)

- **ADR-001: Clean Architecture vs DDD.** Выбираем строгую Clean Architecture (Presentation, Application, Domain, Infrastructure) без сложных концепций DDD (Aggregate Roots, Domain Events) для упрощения монолита.
- **ADR-002: SSE vs WebSocket.** Используем Server-Sent Events (SSE) для стриминга ответов агента, статусов и токенов. Это проще, надежнее и идеально ложится на HTTP/REST архитектуру FastAPI.
- **ADR-003: Blob Storage.** Все файлы (MD пользователя, LaTeX шаблоны, скомпилированные PDF/TEX артефакты) хранятся в MinIO. В Postgres хранятся только метаданные и ссылки (MinIO paths).
- **ADR-004: LaTeX Sandbox.** Компиляция LaTeX происходит в изолированном Podman-контейнере (sandbox) для предотвращения RCE-уязвимостей.
- **ADR-005: Agent Skills & Knowledge.** Файлы пользователя — это "Knowledge Sources". Агент использует их описания как "Skills" для динамического выбора контекста (Tool Calling).
- **ADR-006: Containerization.** Используем `podman` и `podman-compose` вместо Docker. Архитектура должна быть готова к переносу в Kubernetes.



## 3. Requirements Spec (User Stories & Acceptance Criteria)



### Epic 1: Auth & Settings

- **US1.1:** Как пользователь, я хочу входить через Google OAuth.
  - *AC:* Access Token (15 мин) в памяти фронтенда, Refresh Token (30 дней) в HttpOnly Cookie. Поддержка Desktop/Mobile.
- **US1.2:** Как пользователь, я хочу настроить свои LLM (Host, API Key) и выбрать Default LLM.
  - *AC:* Данные шифруются в БД. Можно переопределить LLM перед конкретной генерацией.
- **US1.3:** Как Админ, я хочу блокировать пользователей.
  - *AC:* Наличие UI админки. Заблокированный пользователь получает 403 при любом запросе.



### Epic 2: Knowledge Base & Templates

- **US2.1:** Как пользователь, я хочу загружать MD-файлы с описанием.
  - *AC:* Лимиты на кол-во файлов и размер (из ENV). Хранение в MinIO, метаданные в БД.
- **US2.2:** Как пользователь, я хочу загрузить свой LaTeX шаблон.
  - *AC:* Шаблон сохраняется как базовый скелет для генерации.



### Epic 3: Chat & Agent

- **US3.1:** Как пользователь, я хочу отправить текст вакансии.
  - *AC:* Агент парсит текст, выделяя компанию, стек, требования. Генерирует название чата.
- **US3.2:** Как пользователь, я хочу, чтобы агент задал мне недостающие вопросы.
  - *AC:* ReAct-агент анализирует вакансию и базу знаний, формирует список вопросов.
- **US3.3:** Как пользователь, я хочу видеть процесс "мышления" агента.
  - *AC:* Стриминг SSE событий: статусы, токены, шаги.
- **US3.4:** Как пользователь, я хочу запросить генерацию Cover Letter.
  - *AC:* Отдельная сущность, генерируется только по явному промпту.



## 4. UX / Flow Spec

1. **Onboarding:** Login (Google) -> Настройка LLM API -> Загрузка MD файлов -> Загрузка LaTeX шаблона.
2. **Dashboard:** Sidebar (New Chat, Recent Chats). Основная область пуста (Empty State с подсказкой "Вставьте текст вакансии").
3. **Chat Flow:**
  - User вставляет текст вакансии.
  - AI (Streaming): `[Parsing Vacancy]... [Selecting Context]... [Formulating Questions]`.
  - AI задает вопросы -> User отвечает.
  - User: "Генерируй Resume".
  - AI (Streaming): `[Generating TeX]... [Compiling PDF]... [Uploading]`.
  - Появляется карточка Artifact с кнопкой "Скачать PDF".
4. **Error States:** Ошибка компиляции LaTeX (показать TeX лог), ошибка LLM API (кнопка "Retry" или сменить модель).



## 5. Data Model Spec (PostgreSQL)

```sql
-- Роли: USER, ADMIN
CREATE TABLE users (
    id UUID PRIMARY KEY,
    google_id VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    role VARCHAR DEFAULT 'USER',
    is_blocked BOOLEAN DEFAULT FALSE,
    default_llm_id UUID,
    created_at TIMESTAMP
);

CREATE TABLE llm_configs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider VARCHAR NOT NULL, -- openai, anthropic, ollama, custom
    host VARCHAR,
    api_key_encrypted BYTEA NOT NULL,
    is_default BOOLEAN DEFAULT FALSE
);

CREATE TABLE knowledge_files (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR NOT NULL,
    description TEXT NOT NULL, -- Используется Агентом для выбора скилла
    minio_path VARCHAR NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE latex_templates (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR,
    minio_path VARCHAR NOT NULL
);

CREATE TABLE chats (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR, -- Генерируется LLM
    created_at TIMESTAMP
);

CREATE TABLE messages (
    id UUID PRIMARY KEY,
    chat_id UUID REFERENCES chats(id),
    role VARCHAR NOT NULL, -- user, assistant, system
    content TEXT,
    token_usage JSONB, -- {prompt_tokens, completion_tokens}
    created_at TIMESTAMP
);

CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    chat_id UUID REFERENCES chats(id),
    type VARCHAR NOT NULL, -- resume_pdf, resume_tex, cover_letter_pdf, cover_letter_tex
    minio_path VARCHAR NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE global_prompts (
    id UUID PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL, -- vacancy_parser, context_selector, latex_generator
    content TEXT NOT NULL,
    updated_by UUID REFERENCES users(id) -- Admin
);
```



## 6. Design Spec (Clean Architecture)



### Слои

1. **Domain:** Сущности (`User`, `Chat`, `Artifact`), интерфейсы репозиториев (`IUserRepository`), интерфейсы сервисов (`ILLMProvider`, `IMinioStorage`, `ILatexCompiler`). *Никаких внешних зависимостей.*
2. **Application:** Use Cases (`CreateChatUseCase`, `GenerateResumeUseCase`, `ParseVacancyUseCase`). Оркестрируют доменные объекты и вызывают инфраструктуру через интерфейсы.
3. **Infrastructure:** Реализации интерфейсов (`PostgresUserRepository`, `MinioStorage`, `LangGraphAgent`, `PodmanLatexCompiler`, `OpenAIClient`).
4. **Presentation:** FastAPI роутеры, SSE-эндпоинты, Pydantic схемы, JWT-зависимости.



### Архитектура LangGraph Агента

Граф состояний (StateGraph):

1. `VacancyParserNode`: Вызывает Skill парсинга вакансии.
2. `ContextRetrieverNode`: Анализирует описания `knowledge_files`, выбирает нужные, читает их из MinIO.
3. `QuestionerNode`: Формирует вопросы пользователю (если данных не хватает).
4. `GeneratorNode`: Пишет TeX код на основе шаблона и контекста.
5. `CompilerNode`: Отправляет TeX в Podman Sandbox, получает PDF, загружает в MinIO.
6. `PublisherNode`: Сохраняет Artifact в БД и стримит событие `artifact_created`.



## 7. API Contract Spec (REST + SSE)



### REST Endpoints

- `POST /api/v1/auth/google`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/users/me/llm-configs`
- `POST /api/v1/knowledge-files` (Multipart)
- `POST /api/v1/chats`
- `GET /api/v1/chats/{id}/messages`
- `GET /api/v1/artifacts/{id}/download` (Пресigned URL от MinIO)



### SSE Endpoint

- `POST /api/v1/chats/{id}/stream`
  - Request: `{"message": "text", "llm_config_id": "uuid"}`
  - Response (SSE Format):
    ```text
    event: step_started
    data: {"step": "parsing_vacancy", "timestamp": 1690000000}

    event: status
    data: {"message": "Анализирую требования к стеку...", "tokens_used": 150}

    event: assistant_delta
    data: {"content": "Для этой вакансии мне не хватает информации о вашем опыте с "}

    event: artifact_created
    data: {"artifact_id": "uuid", "type": "resume_pdf", "url": "/api/v1/artifacts/uuid/download"}

    event: done
    data: {"message_id": "uuid"}
    ```



## 8. Security Spec

- **AuthN:** Google OAuth 2.0. JWT Access (RS256), Refresh (HttpOnly, Secure, SameSite=Strict).
- **AuthZ:** Middleware проверки `is_blocked`. Проверка `user_id == resource.user_id` во всех Use Cases (защита от IDOR).
- **PII/Secrets:** API ключи LLM шифруются (Fernet/AES) перед сохранением в Postgres.
- **Sandbox:** LaTeX компиляция в Podman с отключенным сетевым доступом (`--network=none`) и лимитами CPU/RAM.



## 9. Observability Spec

- **Логирование:** Структурированные JSON логи (Python `structlog`).
- **Сбор:** Promtail -> **Loki**.
- **Трейсинг:** Correlation ID (UUID) генерируется на уровне FastAPI Middleware и пробрасывается во все слои, включая LangGraph и Podman-sandbox.



## 10. Test Spec

- **Unit:** Тестирование Application Use Cases с моками Infrastructure интерфейсов.
- **Integration:** `pytest` + `testcontainers` (Postgres, MinIO). Проверка сохранения артефактов.
- **Agent Tests:** Мокирование LLM провайдера для проверки логики переходов в LangGraph (Router -> Parser -> Generator).
- **E2E:** Playwright для UI (логика чата, стриминг SSE).



## 11. Traceability Matrix (Пример)


| Requirement          | Design Component                       | Test Case                          |
| -------------------- | -------------------------------------- | ---------------------------------- |
| US2.1 (MD Files)     | `KnowledgeFile` entity, `MinioStorage` | `test_upload_knowledge_file`       |
| US3.3 (Agent Stream) | `GenerateResumeUseCase`, SSE Router    | `test_sse_events_sequence`         |
| ADR-004 (Sandbox)    | `PodmanLatexCompiler`                  | `test_latex_compilation_isolation` |




## 12. Task Breakdown / Implementation Plan

1. **Phase 1: Skeleton & Infra.** Podman-compose (FastAPI, Postgres, MinIO, Loki). Настройка Clean Architecture слоев.
2. **Phase 2: Auth & Core.** Google OAuth, JWT, Users, Admin block.
3. **Phase 3: Knowledge & Templates.** MinIO интеграция, загрузка MD и LaTeX.
4. **Phase 4: LLM Integration.** Провайдеры, шифрование ключей, глобальные промпты.
5. **Phase 5: LangGraph Agent.** Skills, Nodes, Sandbox компиляция.
6. **Phase 6: Frontend (Vite).** UI чата, SSE клиент, Sidebar.



## 13. Prompt Engineering Spec

*Все промпты хранятся в БД (*`global_prompts`*), редактируются Админом.*

- **Vacancy Parser:** "Extract company, tech stack, hard skills, soft skills from the text. Return JSON."
- **Context Selector:** "Given the vacancy and user's file descriptions, return a list of file IDs to read."
- **LaTeX Generator:** "You are a LaTeX expert. Inject the provided JSON data into the user's LaTeX template. Do not break the template structure."
- **Chat Title Generator:** "Summarize the vacancy in 3-5 words for a chat title."



## 14. Repository Structure Spec

```text
backend/
├── domain/          # Entities, Interfaces (Ports)
├── application/     # Use Cases, DTOs
├── infrastructure/  # DB, MinIO, LangGraph, LLM Clients, Podman
├── presentation/    # FastAPI routers, SSE, Dependencies
├── config/          # ENV, Settings
frontend/
├── src/
│   ├── components/  # UI (Chat, Sidebar, Artifacts)
│   ├── hooks/       # useSSE, useAuth
│   ├── services/    # API clients
docs/                # Design Docs
deployment/          # Podman-compose, Dockerfiles, Sandbox configs
```

---

---



# 🤖 INSTRUCTIONS FOR AI EXECUTORS (LLM Developers)

Ниже представлены три файла, которые должны лежать в корне репозитория. Они служат "операционной памятью" для любой LLM (Cursor, Copilot, Claude), подключающейся к проекту.

### 📄 File 1: `AGENTS.md`

```markdown
# AI Agent Instructions

You are an expert Python/FastAPI and LangGraph developer working on a Production-Grade AI Resume Generator.

## Core Principles
1. **Spec Driven Development:** Never write code without checking the `docs/` folder first. Requirements and Architecture dictate the code, not vice versa.
2. **Strict Clean Architecture:** Dependencies point INWARDS. `Infrastructure` implements `Domain` interfaces. `Application` orchestrates. `Presentation` handles HTTP/SSE.
3. **SOLID:** Single Responsibility is paramount. Use cases must do one thing.
4. **No DDD:** Do not use Aggregate Roots or Domain Events. Keep it simple Clean Architecture.

## Technology Stack
- **Backend:** Python 3.11+, FastAPI, Pydantic V2, SQLAlchemy 2.0 (async), LangGraph.
- **Storage:** PostgreSQL (Metadata), MinIO (Blobs: MD, TeX, PDF).
- **Infra:** Podman (NOT Docker), Loki (Logging).
- **Frontend:** Vite, React, TypeScript, Tailwind/shadcn.

## Boundaries
- NEVER import `infrastructure` or `presentation` modules into `domain` or `application`.
- NEVER execute LaTeX compilation directly. ALWAYS use the `PodmanLatexCompiler` sandbox.
- NEVER store file contents in PostgreSQL. Store MinIO paths.
- NEVER hardcode LLM prompts. Fetch them from the `global_prompts` repository.
```



### 📄 File 2: `ARCHITECTURE.md`

```markdown
# System Architecture

## Layers
1. **Domain (`backend/domain/`)**
   - Pure Python dataclasses/Pydantic models.
   - Interfaces (e.g., `IUserRepository`, `ILLMProvider`, `IMinioStorage`).
   - NO external libraries (no SQLAlchemy, no FastAPI).
2. **Application (`backend/application/`)**
   - Use Cases (e.g., `GenerateResumeUseCase`).
   - Takes Domain interfaces as constructor dependencies.
   - Returns DTOs.
3. **Infrastructure (`backend/infrastructure/`)**
   - Implementations of Domain interfaces.
   - LangGraph Agent definition and Tools (Skills).
   - Podman Sandbox execution logic.
   - MinIO and Postgres clients.
4. **Presentation (`backend/presentation/`)**
   - FastAPI Routers.
   - SSE (Server-Sent Events) generators.
   - JWT/Auth dependencies.

## Agent Flow (LangGraph)
`User Message` -> `Vacancy Parser` -> `Context Retriever (RAG on MD descriptions)` -> `Questioner` -> `LaTeX Generator` -> `Podman Compiler` -> `Artifact Publisher` -> `SSE Stream`.
```

