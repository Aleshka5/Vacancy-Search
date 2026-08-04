# ADR-006: Containerization with Podman

## Status
**Accepted**

## Date
2026-08-04

## Context
We need to decide on containerization and orchestration for the project. The system consists of multiple services:
- FastAPI backend
- PostgreSQL (metadata)
- MinIO (blob storage)
- Podman sandbox (LaTeX compilation)
- Loki (logging, future)
- Frontend (Vite/React, served by Caddy)

Options considered:
- **Docker + docker-compose**: Industry standard, but requires root privileges by default.
- **Podman + podman-compose**: Rootless, Linux-native, Docker-compatible CLI.
- **Kubernetes (K8s)**: Production-grade, but complex for a single-service monolith.
- **Docker → K8s migration**: Start with Docker, migrate to K8s later.

## Decision
We use **Podman + podman-compose** as the primary containerization layer, with **K8s-ready architecture**.

### Why Podman over Docker?
- **Rootless**: No root privileges required — works on any Linux user.
- **Linux-native**: No VM overhead (Docker Desktop), better performance on Linux.
- **Docker-compatible**: `podman-compose` uses the same `docker-compose.yml` format.
- **Security**: No daemon process, better isolation.
- **Future-proof**: Podman has built-in K8s support (`podman kube generate`).

### Architecture
```
podman-compose.yml
├── backend (FastAPI)
├── postgres (metadata)
├── minio (blob storage)
└── sandbox (LaTeX compilation — per-need containers)
```

### K8s-Readiness
- Use standard K8s manifest patterns (Deployments, Services, ConfigMaps, Secrets).
- Podman can generate K8s YAML: `podman kube generate <pod>`.
- All services use environment variables (no hardcoded configs).
- Stateless services where possible (backend, frontend).
- Stateful services configured as K8s StatefulSets (postgres, minio).

## Consequences
- **Positive:**
  - Rootless — no sudo required, works on any user's machine.
  - Development and production use the same tool (podman).
  - `podman-compose` supports the same Compose V2 format.
  - Easy migration to K8s when the project scales.
  - Better security (no daemon, rootless, seccomp by default).
- **Negative:**
  - Smaller ecosystem than Docker (fewer tutorials, tools).
  - Some Docker-specific tools may need Podman equivalents.
  - `podman-compose` is less mature than `docker-compose`.
- **Rules:**
  - Use `podman-compose` for local development (`make dev`).
  - Keep `docker-compose.yml` compatible (it IS the podman-compose format).
  - All services should start with `podman-compose up`.
  - Future K8s manifests should be generated from the same compose file.

## Authors
Vacancy-Search Team

## References
- [Master Document §ADR-006](../docs/Master%20Document.md#6-containerization)
- [Master Document §1: Product Brief](../docs/Master%20Document.md#1-product-brief--vision)
