# US3.1: Send Vacancy Text

## Status
**Proposed**

## Story
**As a** user, I want to send text of a vacancy, so that the agent can analyze it and prepare for resume generation.

## Acceptance Criteria

- [ ] **AC1:** User can paste text of a vacancy into the chat
- [ ] **AC2:** Agent parses the text, extracting: company, tech stack, hard skills, soft skills
- [ ] **AC3:** Agent generates a chat title from the vacancy
- [ ] **AC4:** Parsed data is stored as a message in the chat

## Technical Details

### Backend
- `POST /api/v1/chats` — Create chat (optional, can be auto-created)
- `POST /api/v1/chats/{id}/messages` — Send vacancy text
- Agent parses text via `VacancyParserNode`

### Parsing Output (JSON)
```json
{
    "company": "Acme Corp",
    "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
    "hard_skills": ["REST APIs", "SQL", "Docker"],
    "soft_skills": ["Communication", "Teamwork"],
    "experience_level": "Senior",
    "location": "Remote"
}
```

### Chat Title Generation
- `ChatTitleGeneratorNode` summarizes vacancy in 3-5 words
- Uses `global_prompts.chat_title_generator` prompt
- Stored in `chats.title` field

### Data Model
```sql
CREATE TABLE chats (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR,
    created_at TIMESTAMP
);

CREATE TABLE messages (
    id UUID PRIMARY KEY,
    chat_id UUID REFERENCES chats(id),
    role VARCHAR NOT NULL,
    content TEXT,
    token_usage JSONB,
    created_at TIMESTAMP
);
```

## References
- [Master Document §3 — US3.1](../../docs/Master%20Document.md#us31)
- [Master Document §5 — Data Model Spec](../../docs/Master%20Document.md#5-data-model-spec-postgresql)
- [Master Document §6 — Agent Flow](../../docs/Master%20Document.md#3-agent-flow-langgraph)
- [Master Document §13 — Prompt Engineering](../../docs/Master%20Document.md#13-prompt-engineering-spec)

## Definition of Done (DoD)
- [ ] User can send vacancy text to a chat
- [ ] Agent extracts company, tech stack, skills
- [ ] Chat title generated automatically
- [ ] Parsed data stored as message
- [ ] Unit tests: vacancy parsing logic
- [ ] Integration tests: chat/message endpoints
- [ ] Agent tests: parsing with mocked LLM
- [ ] Error handling: empty text, very long text
- [ ] Frontend UI for pasting text

---

*US generated from Master Document §3, 2026-08-04*
