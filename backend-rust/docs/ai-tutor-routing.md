# AI Tutor Routing Decisions

This document records the routing strategy for all Live AI Teacher and AI Tutor
routes. These routes are **permanently pinned to `gateway`** mode during the
strangler-fig migration because they depend on the Python AI worker process
(LLM orchestration, embedding lookups, streaming chat) which has no native Rust
equivalent planned.

## Routing Strategy

| Route | Method | Mode | Reason |
|-------|--------|------|--------|
| `/api/v1/live/sessions` | GET | gateway | Live session listing — Python AI worker |
| `/api/v1/live/sessions` | POST | gateway | Create live session — Python AI worker |
| `/api/v1/live/sessions/active` | GET | gateway | Active live sessions — Python AI worker |
| `/api/v1/live/sessions/end` | POST | gateway | End live session — Python AI worker |
| `/api/v1/live/chat` | POST | gateway | Send chat message — LLM orchestration |
| `/api/v1/live/chat/history` | GET | gateway | Chat history — Python AI worker |
| `/api/v1/live/feedback` | POST | gateway | Submit feedback — Python AI worker |
| `/api/v1/ai-tutor/status` | GET | gateway | AI tutor status — Python AI worker |
| `/api/v1/ai-tutor/ask` | POST | gateway | Ask AI tutor — LLM orchestration |
| `/api/v1/ai-tutor/explain` | POST | gateway | Request explanation — LLM orchestration |
| `/api/v1/ai-tutor/hint` | POST | gateway | Request hint — LLM orchestration |
| `/api/v1/ai-tutor/conversation` | GET | gateway | Get conversation — Python AI worker |
| `/api/v1/ai-tutor/conversation` | DELETE | gateway | Clear conversation — Python AI worker |

## Rationale

1. **LLM Dependency**: These routes invoke large language models via the Python
   `ai_teacher_agent` service. The orchestration logic (prompt templates, context
   assembly, streaming SSE) lives in Python and is tightly coupled to the AI
   worker's internal state.

2. **No Native Rewrite Planned**: Rewriting the AI orchestration layer in Rust
   is out of scope for this migration. The Python AI worker will continue to run
   as a separate service (`ai_teacher_agent` in docker-compose).

3. **Gateway Pinning**: The Rust dispatcher forwards these requests byte-for-byte
   to the Python upstream. The `route-modes.toml` entries ensure the dispatcher
   never attempts native handling even if a handler is accidentally registered.

4. **CI Enforcement**: The `ai-tutor-pinning` CI lint verifies that every route
   listed in this document is pinned `gateway` in `route-modes.toml`. Any drift
   fails the build.

## Post-Cutover Behavior

After full cutover (Phase 16), the Python `api` service is removed but the
`ai_teacher_agent` service remains. The gateway proxy target for these routes
will be updated to point directly at the AI worker's HTTP interface rather than
the general Python API.
