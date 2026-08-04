# US2.1: Upload Knowledge Files

## Status
**Proposed**

## Story
**As a** user, I want to upload Markdown files with descriptions, so that the agent has knowledge about me to reference during resume generation.

## Acceptance Criteria

- [ ] **AC1:** User can upload MD files via the frontend
- [ ] **AC2:** User provides a description for each file (required field)
- [ ] **AC3:** File size limit enforced (configurable via ENV)
- [ ] **AC4:** File count limit enforced (configurable via ENV)
- [ ] **AC5:** Files stored in MinIO, metadata stored in PostgreSQL
- [ ] **AC6:** User can list, view, and delete their knowledge files

## Technical Details

### Backend
- `POST /api/v1/knowledge-files` (Multipart) — Upload file
- `GET /api/v1/users/me/knowledge-files` — List user's files
- `GET /api/v1/knowledge-files/{id}` — Get file details (metadata)
- `DELETE /api/v1/knowledge-files/{id}` — Delete file

### Upload Endpoint
```python
POST /api/v1/knowledge-files
Content-Type: multipart/form-data

- file: binary MD file
- title: string (required)
- description: string (required, used by Agent as skill description)
```

### Storage
- MinIO path: `knowledge/{user_id}/{file_id}.md`
- Metadata in Postgres: `knowledge_files` table

### Data Model
```sql
CREATE TABLE knowledge_files (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    minio_path VARCHAR NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Limits (configurable via ENV)
| Limit | Default | ENV Variable |
|-------|---------|--------------|
| Max file size | 10 MB | `KNOWLEDGE_MAX_SIZE_MB` |
| Max files per user | 100 | `KNOWLEDGE_MAX_COUNT` |
| Max description length | 1000 chars | `KNOWLEDGE_MAX_DESC_LEN` |

## References
- [Master Document §3 — US2.1](../../docs/Master%20Document.md#us21)
- [Master Document §5 — Data Model Spec](../../docs/Master%20Document.md#5-data-model-spec-postgresql)
- [ADR-003 — Blob Storage](../../adr/003-blob-storage.md)
- [ADR-005 — Agent Skills & Knowledge](../../adr/005-agent-skills-knowledge.md)
- [Master Document §11 — Traceability Matrix](../../docs/Master%20Document.md#traceability-matrix-пример)

## Definition of Done (DoD)
- [ ] User can upload MD files with title and description
- [ ] File size limits enforced (returns 413 if exceeded)
- [ ] File count limits enforced (returns 429 if exceeded)
- [ ] Files stored in MinIO, metadata in Postgres
- [ ] User can list and delete their files
- [ ] Description field is required and used by Agent
- [ ] Unit tests: upload logic, validation
- [ ] Integration tests: MinIO upload with testcontainers
- [ ] Error handling: invalid MD, file not found, permission denied
- [ ] Frontend UI for file upload and management

---

*US generated from Master Document §3, 2026-08-04*
