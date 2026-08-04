# ADR-002: SSE vs WebSocket

## Status
**Accepted**

## Date
2026-08-04

## Context
We need a mechanism for the backend to stream responses from the LangGraph agent to the frontend in real-time. The agent generates:
- Status updates (`"Parsing vacancy..."`)
- Token usage information
- Assistant text deltas
- Artifact creation events
- Error signals

Options considered:
- **WebSocket**: Full-duplex, bidirectional communication. More complex, requires connection management, reconnection logic, and often a dedicated WebSocket server.
- **SSE (Server-Sent Events)**: Unidirectional, HTTP-based, built into HTTP/1.1 and HTTP/2. Simpler, native to REST architectures, automatic reconnection.
- **Long Polling**: Simpler than both, but less efficient for streaming.

Our frontend is Vite + React, and we're using FastAPI on the backend. The communication pattern is predominantly **server → client** (agent streaming to user), with occasional client → server messages.

## Decision
We use **Server-Sent Events (SSE)** for streaming.

### Implementation
- Endpoint: `POST /api/v1/chats/{id}/stream`
- Server streams SSE events in the standard format:
  ```
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

### Event Types
| Event | Description |
|-------|-------------|
| `step_started` | A new processing step begins |
| `status` | Status message with progress info |
| `assistant_delta` | Incremental text content |
| `artifact_created` | New artifact (PDF/TEX) available |
| `done` | Stream completion |
| `error` | Error occurred |

## Consequences
- **Positive:**
  - Simpler than WebSocket — no connection management, no pong/keepalive overhead.
  - Works natively with HTTP/REST — FastAPI supports SSE generators.
  - Browser `EventSource` API provides automatic reconnection.
  - Ideal for our predominantly unidirectional communication pattern.
  - Lower latency for streaming text deltas compared to long polling.
- **Negative:**
  - Unidirectional only (server → client). If we need client → server streaming (e.g., voice input), we'd need a separate channel.
  - No true full-duplex — client sends requests, server pushes events.
  - Limited to text payloads (no binary streaming without base64 encoding).
- **Rules:**
  - All streaming endpoints MUST follow the SSE event format defined in the API Contract.
  - Correlation ID (UUID) propagates through all SSE events for tracing.

## Authors
Vacancy-Search Team

## References
- [Master Document §7: API Contract Spec (REST + SSE)](../docs/Master%20Document.md#7-api-contract-spec-rest--sse)
- [Master Document §3: Agent Flow](../docs/Master%20Document.md#3-agent-flow-langgraph)
