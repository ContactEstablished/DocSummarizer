# TASKS.md — AI Document Summarizer

## New Machine Setup

```bash
# 1. Clone
git clone https://github.com/ContactEstablished/DocSummarizer.git
cd DocSummarizer

# 2. Install backend deps (requires Python 3.11+ and uv)
cd backend
copy .env.example .env    # Windows — then edit .env and set ANTHROPIC_API_KEY
uv sync

# 3. Start the API
uv run doc-summarizer serve   # → http://localhost:8000  |  /docs for Swagger UI

# 4. Install frontend deps (requires Node 20+)
cd ../frontend
npm install
npm run dev   # → http://localhost:5173
```

---

## Project Overview

A local Python application that watches a folder for new documents (PDF, DOCX, TXT, MD),
summarizes them using the Anthropic Claude API, stores summaries in a searchable SQLite
database, and exposes a REST API + Vue.js web UI for browsing and searching summaries.

**Repo:** https://github.com/ContactEstablished/DocSummarizer  
**Stack:** Python 3.11 / FastAPI / SQLAlchemy 2 async / Anthropic SDK · Vue 3 / Vite / TypeScript / Tailwind CSS / Pinia

---

## What Has Already Been Built

Everything below is committed and on `main`.

### Backend (`backend/`)
- [x] FastAPI app (`main.py`) with `lifespan` context manager pattern, CORS, logging
- [x] Pydantic-settings config (`config.py`) — reads from `.env` in CWD
- [x] Structured logging (`logging_config.py`) — console + rotating file handler (5 MB × 5 files → `backend/logs/`)
- [x] SQLAlchemy 2 async models (`db/models.py`) — `Summary` table
- [x] Async session factory + `init_db()` (`db/session.py`) — auto-creates `data/` dir
- [x] Repository layer (`db/repository.py`) — `get_all`, `get_by_id`, `get_by_hash`, `create`, `delete`, `search` (all with efficient `func.count()`)
- [x] Pydantic v2 schemas (`schemas/summary.py`) — `SummaryResponse`, `SummaryPage`
- [x] Document parser dispatch (`core/parser.py`) — routes by extension
- [x] PDF / DOCX / Text parsers in `core/parsers/`
- [x] Anthropic summarizer (`core/summarizer.py`) — retries on rate-limit / transient errors (tenacity, exponential backoff 2 s → 60 s, 4 attempts); strips markdown fences before JSON parse
- [x] Watchdog file watcher (`core/watcher.py`)
- [x] `to_response()` helper (`api/utils.py`) — single conversion point ORM → Pydantic
- [x] REST endpoints: `GET /api/health`, `GET|POST /api/summaries`, `GET|DELETE /api/summaries/{id}`, `POST /api/summaries/upload`, `GET /api/search`
- [x] Click CLI: `doc-summarizer serve|watch|summarize`
- [x] `pyproject.toml` with all deps + `uv.lock`
- [x] `.env.example` with all required variables
- [x] `backend/data/watch/` and `backend/logs/` tracked via `.gitkeep`
- [x] 19 passing tests: `test_api.py` (8 async, in-memory SQLite, Anthropic mocked), `test_parser.py` (10 + 1 skipped live test)

### Frontend (`frontend/`)
- [x] Vue 3 + Vite + TypeScript
- [x] Tailwind CSS dark mode — `.card`, `.btn-primary`, `.btn-ghost`, `.badge`, `.input` in `style.css`
- [x] Pinia store (`stores/summaries.ts`)
- [x] Vue Router — `/`, `/summary/:id`, `/search`
- [x] Axios API client (`api/client.ts`)
- [x] `SummaryList.vue` — paginated card grid, confirm-modal delete
- [x] `SummaryDetail.vue` — full summary, metadata, confirm-modal delete
- [x] `Search.vue`
- [x] `FileUpload.vue` — drag-and-drop, animated success/error toast (4 s auto-dismiss)
- [x] `ConfirmModal.vue` — teleported modal, backdrop dismiss, transition animations
- [x] `package-lock.json` committed

### Repo / Config
- [x] `.gitignore`, `.claudeignore` (protects `.env`, `data/`, logs)
- [x] `.claude/settings.json` — tool allowlist for unattended operation
- [x] `README.md` — badges, features, quick-start, API reference
- [x] MIT `LICENSE`

---

## Database Schema

**`summaries` table**

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | auto-increment |
| `file_path` | TEXT UNIQUE | full path or upload filename |
| `file_name` | TEXT | display name |
| `file_type` | TEXT | `pdf`, `docx`, `txt`, `md` |
| `original_size_bytes` | INTEGER | |
| `content_hash` | TEXT | SHA-256, dedup key |
| `summary_short` | TEXT | 2-3 sentence summary |
| `summary_long` | TEXT | paragraph-length summary |
| `key_topics` | TEXT | JSON-encoded array of strings |
| `created_at` | TIMESTAMP | server default |
| `updated_at` | TIMESTAMP | auto-updated |

---

## Remaining Work — Sprint 2

### 🔴 High Value

- [ ] **Re-summarize button** — detail page button that re-calls Claude on the stored document text and updates the DB record. Needs a new `PATCH /api/summaries/{id}/re-summarize` endpoint and frontend button with loading state.

- [ ] **Sort & filter on library page** — add controls to sort by date / name / file size and filter by file type (`pdf`, `docx`, `txt`, `md`). Backend: add optional `sort`, `order`, `file_type` query params to `GET /api/summaries`. Frontend: filter/sort toolbar above the grid.

- [ ] **Copy summary to clipboard** — "Copy" button on the detail view and summary cards. Use the Clipboard API; show a brief "Copied!" tooltip confirmation.

- [ ] **Batch upload** — allow selecting multiple files at once in `FileUpload.vue`. Upload sequentially (to avoid hammering the API); show per-file progress and a summary count when done.

- [ ] **"Ask a question" mode** — on the detail page, a text input that sends the stored `summary_long` + user question to Claude and streams the answer. New `POST /api/summaries/{id}/ask` endpoint. Frontend: expandable Q&A panel with streaming response display.

### 🟡 Developer Experience / Ops

- [ ] **Docker Compose** — `docker-compose.yml` with `backend` and `frontend` services. Backend image: `python:3.11-slim` + uv; frontend image: Node build stage + nginx static serve. `.env` mounted as a volume secret.

- [ ] **SQLite FTS5 full-text search** — replace the current `LIKE` search in `repository.py` with a `summaries_fts` virtual table. Add a migration step in `init_db()` to create the FTS table and keep it in sync via triggers. Dramatically faster on large document libraries.

- [ ] **Export to Markdown** — "Export" button on detail page that downloads a `.md` file containing filename, metadata, short summary, long summary, and key topics. Pure frontend — no backend endpoint needed.

### 🟢 Stretch Goals

- [ ] **Folder watcher UI integration** — a WebSocket endpoint (`GET /api/ws/events`) that broadcasts new-summary events. Frontend subscribes on mount and auto-refreshes the library when a new summary arrives from the watcher.

- [ ] **Prompt customization UI** — a settings panel where the user can edit the system prompt sent to Claude and choose the model / max tokens. Store in `localStorage`; send as optional request body fields on upload.

- [ ] **OCR support** — image-only PDF fallback via `pytesseract` + `pdf2image` when `pypdf` returns blank text.

- [ ] **Multi-user auth** — JWT-based auth (FastAPI-Users or hand-rolled) with per-user summary isolation.

---

## Notes for Claude Code

- Python 3.11+ syntax throughout — use `X | Y` unions, `match` where appropriate
- **All DB access must be async** — no sync SQLAlchemy calls anywhere
- Pydantic v2 syntax for schemas (`model_config`, not `class Config`)
- Use `FastAPI Depends()` for injection — no new module-level singletons (except `settings`)
- The Anthropic client lives in `core/summarizer.py` — extend there, do not create a second instance
- `key_topics` is a JSON string in SQLite — always use `json.dumps` / `json.loads`; `to_response()` already handles this for existing routes
- Frontend: use `@/` import alias; prefer the `@layer components` utility classes in `style.css`
- Tests: `conftest.py` sets a dummy `ANTHROPIC_API_KEY` so no real key is needed; mock `_call_api` (not the full client) in new API tests
