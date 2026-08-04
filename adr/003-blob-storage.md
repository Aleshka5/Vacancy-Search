# ADR-003: Blob Storage with MinIO

## Status
**Accepted**

## Date
2026-08-04

## Context
We need to store several types of files:
- User's Markdown knowledge files
- LaTeX templates
- Generated PDF artifacts (Resume/Cover Letter)
- Generated TEX source files
- Temporary files during compilation

Options considered:
- **Postgres BLOB columns**: Store files directly in the database. Simple but inefficient for large files, increases DB size, slow queries.
- **S3-compatible object storage (MinIO)**: Purpose-built for blobs, supports presigned URLs, scalable, cloud-agnostic.
- **Local filesystem**: Simplest, but doesn't scale and makes containerization harder.
- **Cloud-specific (S3/GCS/Azure)**: Locked in to one provider.

## Decision
We use **MinIO** as our blob storage layer. PostgreSQL stores only metadata and references (MinIO paths).

### Storage Layout
- `knowledge/{user_id}/{file_id}.md` — User knowledge files
- `templates/{user_id}/{template_id}.tex` — LaTeX templates
- `artifacts/{chat_id}/{artifact_id}.pdf` — Generated PDFs
- `artifacts/{chat_id}/{artifact_id}.tex` — Generated TEX files
- `temp/{sandbox_id}/{file}` — Temporary sandbox files

### Database Schema
```sql
CREATE TABLE knowledge_files (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    minio_path VARCHAR NOT NULL,  -- NOT the content
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE latex_templates (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR,
    minio_path VARCHAR NOT NULL
);

CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    chat_id UUID REFERENCES chats(id),
    type VARCHAR NOT NULL,
    minio_path VARCHAR NOT NULL,
    created_at TIMESTAMP
);
```

## Consequences
- **Positive:**
  - Scalable — MinIO can grow independently of the database.
  - Presigned URLs allow direct browser-to-MinIO downloads without backend proxy.
  - Cloud-agnostic — can swap MinIO for AWS S3, GCS, or Azure Blob Storage.
  - Database stays lean — only metadata stored in Postgres.
  - Easy backup and replication of blob storage.
- **Negative:**
  - Added infrastructure component (need MinIO container in podman-compose).
  - Two systems to manage (Postgres + MinIO) instead of one.
  - Slightly more complex error handling (need to handle MinIO upload failures).
- **Rules:**
  - NEVER store file contents in PostgreSQL. Store MinIO paths only.
  - NEVER store API keys or MD content in Postgres. Use MinIO and encryption.
  - All file operations go through the `IMinioStorage` interface.

## Authors
Vacancy-Search Team

## References
- [Master Document §5: Data Model Spec](../docs/Master%20Document.md#5-data-model-spec-postgresql)
- [Master Document §ADR-003](../docs/Master%20Document.md#3-blob-storage)
