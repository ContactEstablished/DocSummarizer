# TASKS.md — AI Document Summarizer

## Handoff Notes

Development is being continued on a new machine. Clone the repo, follow the
**New Machine Setup** section below, then pick up from **Remaining Work**.

### New Machine Setup

```bash
# 1. Clone
git clone https://github.com/ContactEstablished/DocSummarizer.git
cd DocSummarizer

# 2. Install backend deps  (requires Python 3.11+ and uv)
cd backend
cp .env.example .env          # then edit .env and set ANTHROPIC_API_KEY
uv sync

# 3. Verify the API starts cleanly
uv run doc-summarizer serve   # → http://localhost:8000  |  /docs for Swagger UI

# 4. Install frontend deps  (requires Node 20+)
cd ../frontend
npm install
npm run dev                   # → http://localhost:5173
```

> **Note:** `npm install` and `uv sync` have not been run yet — the lock files
> don't exist. Run them once on the new machine to generate them and commit the
> results (`uv.lock`, `package-lock.json`).

---

## Project Overview

A local Python application that watches a folder for new documents (PDF, DOCX,
TXT, MD), summarizes them using the Anthropic Claude API, stores summaries in a
searchable SQLite database, and exposes both a REST API and a Vue.js web UI for
browsing and searching summaries.

**Repo:** https://github.com/ContactEstablished/DocSummarizer  
**Stack:** Python 3.11 / FastAPI / SQLAlchemy 2 async / Anthropic SDK · Vue 3 / Vite / TypeScript / Tailwind CSS / Pinia

---

## What Has Already Been Built

Everything below is committed and on `main`. Do **not** re-implement these.

### Backend (`backend/`)
- [x] FastAPI app (`main.py`) with CORS configured for the Vue dev server
- [x] Pydantic-settings config (`config.py`) — reads from `.env`
- [x] SQLAlchemy 2 async models (`db/models.py`) — `Summary` table matching the schema below
- [x] Async session factory + `init_db()` (`db/session.py`)
- [x] Repository layer (`db/repository.py`) — `get_all`, `get_by_id`, `get_by_hash`, `create`, `delete`, `search`
- [x] Pydantic v2 schemas (`schemas/summary.py`) — `SummaryResponse`, `SummaryPage`, `SummaryCreate`
- [x] Document parser dispatch (`core/parser.py`) — routes by file extension
- [x] PDF parser via `pypdf` (`core/parsers/pdf_parser.py`)
- [x] DOCX parser via `python-docx` (`core/parsers/docx_parser.py`)
- [x] Text / Markdown parser (`core/parsers/text_parser.py`)
- [x] Anthropic summarizer client (`core/summarizer.py`) — returns `summary_short`, `summary_long`, `key_topics`
- [x] Watchdog file watcher (`core/watcher.py`) — fires async callback on new files
- [x] Shared response helper (`api/utils.py`) — `to_response(Summary) → SummaryResponse`
- [x] REST endpoints (all fully wired, not stubs):
  - `GET  /api/health`
  - `GET  /api/summaries` (paginated)
  - `GET  /api/summaries/{id}`
  - `DELETE /api/summaries/{id}`
  - `POST /api/summaries/upload` (parse → SHA-256 dedup → Claude → persist)
  - `GET  /api/search?q=...`
- [x] Click CLI (`cli.py`):
  - `doc-summarizer serve`
  - `doc-summarizer watch <folder>` (full watchdog loop with async pipeline)
  - `doc-summarizer summarize <file>` (parse + summarize + optional DB save)
- [x] `pyproject.toml` with `uv`, `hatchling` build backend, all deps pinned
- [x] `.env.example` with all required variables documented
- [x] `backend/data/watch/` folder tracked via `.gitkeep`

### Frontend (`frontend/`)
- [x] Vue 3 + Vite + TypeScript scaffold
- [x] Tailwind CSS — dark mode by default, custom `brand` color palette, reusable `.card`, `.btn-primary`, `.badge` utility classes in `style.css`
- [x] Pinia store (`stores/summaries.ts`) — `fetchPage`, `deleteSummary`, `uploadFile`
- [x] Vue Router — `/` (list), `/summary/:id` (detail), `/search`
- [x] Axios API client (`api/client.ts`) — typed wrappers for every endpoint
- [x] `SummaryList.vue` — paginated card grid, skeleton loaders, empty state
- [x] `SummaryDetail.vue` — full summary, metadata, delete
- [x] `Search.vue` — query-string-driven search, result count
- [x] `SummaryCard.vue` — file icon, short summary, topic badges, metadata footer
- [x] `SearchBar.vue` — navigates to `/search?q=...` on submit
- [x] `FileUpload.vue` — drag-and-drop + click-to-browse, shows upload progress
- [x] `App.vue` — sticky nav header, responsive layout

### Repo / Config
- [x] `.gitignore` — Python, Node, `.env`, `data/`, SQLite files
- [x] `README.md` — badges, features, tech stack, quick-start, API reference, project tree
- [x] MIT `LICENSE`

---

## Database Schema (implemented)

**`summaries` table**

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | auto-increment |
| `file_path` | TEXT UNIQUE | full path or upload filename |
| `file_name` | TEXT | display name |
| `file_type` | TEXT | `pdf`, `docx`, `txt`, `md` |
| `original_size_bytes` | INTEGER | |
| `content_hash` | TEXT | SHA-256, used for dedup |
| `summary_short` | TEXT | 2-3 sentence summary |
| `summary_long` | TEXT | paragraph-length summary |
| `key_topics` | TEXT | JSON array of topic strings |
| `created_at` | TIMESTAMP | server default |
| `updated_at` | TIMESTAMP | auto-updated |

---

## Remaining Work

### 🔴 Must-Do Before V1 is Usable

- [ ] **Run `uv sync` and commit `uv.lock`** — lock file doesn't exist yet; do this first
- [ ] **Run `npm install` and commit `package-lock.json`** — same reason
- [ ] **Fix FastAPI startup deprecation** — `@app.on_event("startup")` is deprecated in FastAPI 0.115+. Replace with the `lifespan` context manager pattern in `main.py`:
  ```python
  from contextlib import asynccontextmanager
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      await init_db()
      yield
  app = FastAPI(..., lifespan=lifespan)
  ```
- [ ] **Add retry / rate-limit handling to `summarizer.py`** — currently a bare API call with no error handling. Wrap with exponential backoff (use `tenacity` or manual retry loop) for `anthropic.RateLimitError` and `anthropic.APIStatusError`
- [ ] **Logging: add rotating file handler** — `config.py` has `log_level` but `main.py` only calls `basicConfig`. Add a `RotatingFileHandler` writing to `backend/logs/doc_summarizer.log`

### 🟡 Quality / Polish

- [ ] **Pass `SummaryResponse` unused import warning** — `SummaryResponse` is imported but only used indirectly in `search.py`; verify no linter warnings after running `uv run ruff check src/`
- [ ] **Frontend: `.env` support for API base URL** — `client.ts` reads `import.meta.env.VITE_API_BASE_URL` but there's no `frontend/.env.example`. Add one:
  ```
  VITE_API_BASE_URL=/api
  ```
- [ ] **Frontend: toast / notification on upload success/error** — currently the `FileUpload` component silently succeeds. Add a brief success toast (a simple `<Transition>` overlay is fine — no extra library needed)
- [ ] **Frontend: confirm dialog component** — `SummaryList` and `SummaryDetail` both use bare `window.confirm()` for delete. Replace with a simple inline modal component
- [ ] **Expand test coverage:**
  - `test_parser.py` has 2 basic tests — add DOCX round-trip test
  - `test_api.py` only tests health — add tests for list (empty DB), upload (mock summarizer), and 404 on unknown ID
  - Mock the Anthropic client in tests so they don't need a live API key

### 🟢 Stretch Goals (discuss before starting)

- [ ] SQLite FTS5 full-text search (replace ILIKE with virtual table for speed)
- [ ] Tag-based filtering in the list view
- [ ] Export a summary to Markdown or PDF
- [ ] OCR support for image-only PDFs via `pytesseract`
- [ ] Batch re-summarization endpoint (re-run Claude on existing documents with a new prompt)
- [ ] "Ask a question" mode — RAG over stored summaries using Claude + embeddings
- [ ] Docker Compose for one-command deployment
- [ ] Multi-user auth

---

## Notes for Claude Code

- Python 3.11+ syntax throughout — use `X | Y` unions, `match` statements where appropriate
- **All DB access must be async** — no sync SQLAlchemy calls
- Pydantic v2 syntax for all schemas (`model_config`, not `class Config`)
- Use `FastAPI Depends()` for injection — no module-level singletons except `settings`
- The Anthropic SDK is already wired in `core/summarizer.py` — extend there, don't create a second client
- Frontend uses `@/` path alias mapped to `src/` — use it for all imports
- Tailwind utilities are defined in `src/style.css` under `@layer components` — prefer those over inline classes for consistency
