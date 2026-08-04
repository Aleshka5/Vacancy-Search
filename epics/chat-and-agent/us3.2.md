# US3.2: Agent Questions

## Status
**Proposed**

## Story
**As a** user, I want the agent to ask me missing questions, so that it can generate a more personalized resume.

## Acceptance Criteria

- [ ] **AC1:** ReAct-agent analyzes the vacancy and knowledge base
- [ ] **AC2:** Agent formulates questions if data is insufficient
- [ ] **AC3:** Questions are displayed as chat messages
- [ ] **AC4:** User can answer questions directly in the chat
- [ ] **AC5:** Agent continues processing after receiving answers

## Technical Details

### Agent Flow
```
VacancyParserNode → ContextRetrieverNode → QuestionerNode → GeneratorNode
                                              ↓
                                       (if missing data)
                                              ↓
                                       QuestionerNode
                                              ↓
                                       User answers
                                              ↓
                                       ContextRetrieverNode (re-evaluate)
                                              ↓
                                       GeneratorNode
```

### Question Generation
- Agent compares vacancy requirements with user's knowledge files
- Identifies gaps (e.g., "I don't see your experience with React")
- Formulates 1-5 questions per vacancy
- Uses `global_prompts.context_selector` prompt

### Question Format
```json
{
    "question": "What was your role when you worked with React?",
    "source": "knowledge_file:resume.md",
    "required": true
}
```

### Data Model
- Questions stored as assistant messages in `messages` table
- Answers stored as user messages
- Agent state tracks pending questions in LangGraph state

## References
- [Master Document §3 — US3.2](../../docs/Master%20Document.md#us32)
- [Master Document §6 — Agent Flow](../../docs/Master%20Document.md#3-agent-flow-langgraph)
- [ADR-005 — Agent Skills & Knowledge](../../adr/005-agent-skills-knowledge.md)

## Definition of Done (DoD)
- [ ] Agent identifies missing information
- [ ] Questions are relevant and specific
- [ ] User can answer in chat
- [ ] Agent continues after answers
- [ ] Unit tests: question generation logic
- [ ] Agent tests: full flow (question → answer → continue)
- [ ] E2E test: Playwright for question/answer flow
- [ ] Error handling: no questions needed, too many questions
- [ ] Frontend UI for displaying questions

---

*US generated from Master Document §3, 2026-08-04*
