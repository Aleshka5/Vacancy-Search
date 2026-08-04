# ADR-001: Clean Architecture vs DDD

## Status
**Accepted**

## Date
2026-08-04

## Context
We needed to choose between two architectural styles for our monolith:
- **Clean Architecture**: Dependency rule with layers (Presentation → Application → Domain ← Infrastructure), ports and adapters.
- **DDD (Domain-Driven Design)**: Aggregate Roots, Domain Events, Domain Services, bounded contexts.

The project is an AI Resume Generator — a service with a well-defined problem space but not complex enough to warrant full DDD. We want to avoid over-engineering while keeping the codebase maintainable as it grows.

## Decision
We choose **strict Clean Architecture** without complex DDD concepts:
- **Domain layer**: Pure Python dataclasses/Pydantic models, interfaces (ports) — no external libraries, no Aggregate Roots, no Domain Events.
- **Application layer**: Use Cases that orchestrate domain objects and call infrastructure via interfaces.
- **Infrastructure layer**: Concrete implementations (Postgres, MinIO, LangGraph, Podman, LLM clients).
- **Presentation layer**: FastAPI routers, SSE generators, JWT dependencies, Pydantic schemas.

We explicitly **exclude** DDD concepts:
- No Aggregate Roots
- No Domain Events
- No Domain Services (use cases handle orchestration)
- No Bounded Contexts (single monolith for now)

## Consequences
- **Positive:**
  - Simpler mental model for developers joining the project.
  - Easy to test — interfaces can be mocked at any layer.
  - Dependencies point inward, so domain is pure and stable.
  - Easy to swap implementations (e.g., swap Postgres for SQLite without touching business logic).
- **Negative:**
  - As the system grows, we may eventually need DDD concepts — but we can add them incrementally.
  - Some use cases may become "fat" without DDD's domain services for complex domain logic.
- **Rules:**
  - NEVER import `infrastructure` or `presentation` into `domain` or `application`.
  - Use `IRepository` interfaces in domain, concrete implementations in infrastructure.

## Authors
Vacancy-Search Team

## References
- [Master Document §6: Design Spec](../docs/Master%20Document.md#6-design-spec-clean-architecture)
- [AGENTS.md: Core Principles](../AGENTS.md)
