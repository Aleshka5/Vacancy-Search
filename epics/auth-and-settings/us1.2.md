# US1.2: LLM Configuration

## Status
**Proposed**

## Story
**As a** user, I want to configure my LLM providers (Host, API Key) and select a Default LLM, so that the agent uses the right model for generation.

## Acceptance Criteria

- [ ] **AC1:** User can add multiple LLM configurations (Host, API Key, Provider)
- [ ] **AC2:** User can set a Default LLM (used for all generations unless overridden)
- [ ] **AC3:** API keys are encrypted in the database (Fernet/AES)
- [ ] **AC4:** User can override LLM before a specific generation
- [ ] **AC5:** User can edit/delete their LLM configurations

## Technical Details

### Backend
- `GET /api/v1/users/me/llm-configs` — List user's LLM configs
- `POST /api/v1/users/me/llm-configs` — Create LLM config
- `PUT /api/v1/users/me/llm-configs/{id}` — Update LLM config
- `DELETE /api/v1/users/me/llm-configs/{id}` — Delete LLM config
- `PATCH /api/v1/users/me/llm-configs/{id}/default` — Set as default

### Encryption
- API keys encrypted with Fernet (symmetric key per user) or AES-GCM
- Encrypted bytes stored in `api_key_encrypted BYTEA` column
- Decryption happens in Application layer before passing to LLM clients

### Data Model
```sql
CREATE TABLE llm_configs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider VARCHAR NOT NULL, -- openai, anthropic, ollama, custom
    host VARCHAR,
    api_key_encrypted BYTEA NOT NULL,
    is_default BOOLEAN DEFAULT FALSE
);
```

### Supported Providers
| Provider | Host Format | Key Format |
|----------|-------------|------------|
| OpenAI | `https://api.openai.com` | `sk-...` |
| Anthropic | `https://api.anthropic.com` | `sk-ant-...` |
| Ollama | `http://host:11434` | (empty) |
| Custom | User-defined | User-defined |

## References
- [Master Document §3 — US1.2](../../docs/Master%20Document.md#us12)
- [Master Document §8 — Security Spec](../../docs/Master%20Document.md#8-security-spec)
- [ADR-003 — Blob Storage](../../adr/003-blob-storage.md)

## Definition of Done (DoD)
- [ ] User can add/edit/delete LLM configs
- [ ] Default LLM is correctly applied to all generations
- [ ] Override works per-generation
- [ ] API keys are encrypted in database (verify by checking DB)
- [ ] All 4 providers (OpenAI, Anthropic, Ollama, Custom) work
- [ ] Unit tests: encryption/decryption, config validation
- [ ] Integration tests: LLM config CRUD with testcontainers
- [ ] Frontend UI for LLM config management
- [ ] Error handling: invalid API keys return clear messages

---

*US generated from Master Document §3, 2026-08-04*
