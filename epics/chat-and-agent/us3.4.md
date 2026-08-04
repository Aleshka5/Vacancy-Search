# US3.4: Cover Letter Generation

## Status
**Proposed**

## Story
**As a** user, I want to request Cover Letter generation, so that I can get a personalized letter for each vacancy.

## Acceptance Criteria

- [ ] **AC1:** Cover Letter is a separate entity from Resume
- [ ] **AC2:** Cover Letter is generated only on explicit prompt
- [ ] **AC3:** User can request Cover Letter in the chat
- [ ] **AC4:** Cover Letter is stored as an artifact (PDF + TEX)

## Technical Details

### Backend
- User sends message: "Generate Cover Letter" (or clicks button)
- Agent creates Cover Letter using `GeneratorNode`
- Generates PDF via Podman sandbox (same as Resume)
- Stores artifact in MinIO

### Cover Letter Entity
```sql
CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    chat_id UUID REFERENCES chats(id),
    type VARCHAR NOT NULL, -- resume_pdf, resume_tex, cover_letter_pdf, cover_letter_tex
    minio_path VARCHAR NOT NULL,
    created_at TIMESTAMP
);
```

### Artifact Types
| Type | Description |
|------|-------------|
| `resume_pdf` | Resume PDF |
| `resume_tex` | Resume TEX source |
| `cover_letter_pdf` | Cover Letter PDF |
| `cover_letter_tex` | Cover Letter TEX source |

### Cover Letter Generation Flow
```
User: "Generate Cover Letter"
  ↓
GeneratorNode: Create Cover Letter content
  ↓
CompilerNode: Compile in Podman sandbox
  ↓
PublisherNode: Save artifact to MinIO
  ↓
SSE: artifact_created event sent
```

## References
- [Master Document §3 — US3.4](../../docs/Master%20Document.md#us34)
- [Master Document §5 — Data Model Spec](../../docs/Master%20Document.md#5-data-model-spec-postgresql)
- [ADR-004 — LaTeX Sandbox](../../adr/004-latex-sandbox.md)
- [ADR-003 — Blob Storage](../../adr/003-blob-storage.md)

## Definition of Done (DoD)
- [ ] Cover Letter generation works on explicit prompt
- [ ] Cover Letter is separate from Resume
- [ ] PDF generated via Podman sandbox
- [ ] Artifact stored in MinIO with correct type
- [ ] User can download Cover Letter PDF
- [ ] Unit tests: Cover Letter generation
- [ ] Agent tests: Cover Letter in agent flow
- [ ] Integration tests: artifact storage
- [ ] E2E test: Playwright for Cover Letter flow
- [ ] Frontend UI for Cover Letter request and download

---

*US generated from Master Document §3, 2026-08-04*
