# US2.2: Upload LaTeX Templates

## Status
**Proposed**

## Story
**As a** user, I want to upload my own LaTeX template, so that generated resumes use my personal formatting.

## Acceptance Criteria

- [ ] **AC1:** User can upload a LaTeX template file
- [ ] **AC2:** Template is saved as the base skeleton for generation
- [ ] **AC3:** Template is stored in MinIO, metadata in PostgreSQL
- [ ] **AC4:** User can view and delete their templates

## Technical Details

### Backend
- `POST /api/v1/latex-templates` (Multipart) — Upload template
- `GET /api/v1/users/me/latex-templates` — List user's templates
- `GET /api/v1/latex-templates/{id}` — Get template details
- `DELETE /api/v1/latex-templates/{id}` — Delete template

### Upload Endpoint
```python
POST /api/v1/latex-templates
Content-Type: multipart/form-data

- file: binary TEX file
- name: string (optional, defaults to filename)
```

### Storage
- MinIO path: `templates/{user_id}/{template_id}.tex`
- Metadata in Postgres: `latex_templates` table

### Data Model
```sql
CREATE TABLE latex_templates (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR,
    minio_path VARCHAR NOT NULL
);
```

### Template Usage
- Templates are loaded from MinIO during generation
- The agent injects data into the template without breaking its structure
- Template structure is preserved (only data is injected)

## References
- [Master Document §3 — US2.2](../../docs/Master%20Document.md#us22)
- [Master Document §5 — Data Model Spec](../../docs/Master%20Document.md#5-data-model-spec-postgresql)
- [ADR-003 — Blob Storage](../../adr/003-blob-storage.md)

## Definition of Done (DoD)
- [ ] User can upload TEX template files
- [ ] Template is saved and retrievable
- [ ] Template is used as base for generation
- [ ] User can view and delete templates
- [ ] Unit tests: template storage, retrieval
- [ ] Integration tests: MinIO storage with testcontainers
- [ ] Error handling: invalid TEX files
- [ ] Frontend UI for template management
- [ ] Template preview (basic rendering)

---

*US generated from Master Document §3, 2026-08-04*
