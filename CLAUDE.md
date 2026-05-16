# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

DocSummarizer watches a local folder for PDF/DOCX/TXT/MD files, summarizes them with Claude (Anthropic API), stores results in SQLite, and serves them through a FastAPI REST API and a Vue 3 web UI.

## Commands

All backend commands must be run from the `backend/` directory (Settings reads `.env` relative to CWD).

```bash
# Backend — install deps
cd backend && uv sync

# Run the API server (dev, with auto-reload)
uv run doc-summarizer serve --reload

# Run the file watcher
uv run doc-summarizer watch ./data/watch

# Summarize a single file on demand
uv run doc-summarizer summarize path/to/file.pdf

# Lint / format
uv run ruff check src/
uv run ruff format src/

# Run all tests (no real API key needed — conftest.py sets a dummy one)
uv run pytest

# Run a single test file
uv run pytest src/tests/test_api.py

# Run a single test by name
uv run pytest src/tests/test_api.py::test_health_check -v
```

```bash
# Frontend
cd frontend && npm install
npm run dev          # dev server proxying /api → localhost:8000
npm run type-check
npm run build
```

## Architecture

### Backend request flow

```
HTTP request
  → FastAPI route (api/routes/*.py)
  → SummaryRepository (db/repository.py)  ← AsyncSession via Depends(get_db)
  → SQLAlchemy async / aiosqlite
  → api/utils.to_response()               ← converts ORM → Pydantic
  → JSON response
```

Upload pipeline:
```
POST /api/summaries/upload
  → validate extension (pdf, docx, txt, md)
  → SHA-256 hash → check duplicate (return cached if found)
  → write to NamedTemporaryFile
  → core/parser.py dispatch → parser (pdf / docx / text)
  → delete tempfile
  → core/summarizer.summarize_document()   ← SYNCHRONOUS, blocks event loop
  → persist Summary model
  → to_response()
```

### Key architectural facts

**`key_topics` is stored as a JSON string.** The `Summary` ORM model has `key_topics: Mapped[str]`. Always use `json.dumps(list)` when writing and `json.loads(str)` when reading. `api/utils.to_response()` handles this for all current routes — route through that helper.

**`settings` is a module-level singleton** instantiated at import in `config.py`. All env vars are read once at startup from a `.env` file in the CWD. Running backend commands from the wrong directory silently uses wrong paths.

**`summarize_document()` is synchronous.** The Anthropic SDK call blocks the event loop during summarization. This is a known trade-off; do not add `await` to it without switching the SDK call to `AsyncAnthropic`.

**Retry logic** in `core/summarizer.py` uses `tenacity` with exponential backoff (2 s → 60 s, 4 attempts). It retries only on `RateLimitError`, `InternalServerError`, `APIConnectionError`, and `APITimeoutError`. It does **not** retry `AuthenticationError` — that fails immediately on the first attempt.

**Markdown fence stripping** — Claude occasionally wraps its JSON in ` ```json ... ``` ` despite the system prompt. `_strip_markdown_fences()` in `summarizer.py` handles this before `json.loads()`.

**Logging** is configured by `logging_config.py` (called from `main.py` lifespan). Console handler + `RotatingFileHandler` writing to `backend/logs/doc_summarizer.log` (5 MB × 5 files). The `logs/` directory is gitignored except for a `.gitkeep`.

**`.claudeignore`** (repo root) prevents Claude Code from reading `.env` files, `backend/data/`, and log files.

### Testing

Tests live in `backend/src/tests/`. `conftest.py` sets `ANTHROPIC_API_KEY=sk-ant-test-key` so no real key is required. API tests use FastAPI's `dependency_overrides` to inject an in-memory SQLite session and `unittest.mock.patch` on `doc_summarizer.core.summarizer._call_api` to avoid real API calls. Always mock `_call_api` (not the Anthropic client directly) in new tests.

### Frontend architecture

The Vite dev server proxies all `/api` requests to `localhost:8000` (`vite.config.ts`). All API calls go through `src/api/client.ts` (typed Axios wrappers). State lives in `src/stores/summaries.ts` (Pinia). Views own their own local loading/error state for detail and search.

**Tailwind utility classes** (`.card`, `.btn-primary`, `.btn-ghost`, `.badge`, `.input`) are defined under `@layer components` in `src/style.css` — prefer those over ad-hoc inline Tailwind.

The `@/` import alias maps to `frontend/src/`.

### File structure

```
backend/src/doc_summarizer/
  config.py            # pydantic-settings singleton (Settings)
  logging_config.py    # configure_logging() — call once at startup
  main.py              # FastAPI app, lifespan, CORS, router registration
  cli.py               # click CLI: serve / watch / summarize
  api/
    dependencies.py    # get_db() dependency
    utils.py           # to_response() — ORM → schema conversion
    routes/            # summaries.py, search.py, health.py
  core/
    summarizer.py      # Anthropic call (sync) + retry + fence stripping
    parser.py          # dispatch by extension → parsers/
    watcher.py         # watchdog Observer wrapper
  db/
    models.py          # Summary ORM model
    session.py         # engine, async_session_factory, init_db(), _ensure_db_dir()
    repository.py      # SummaryRepository (all DB access)
  schemas/
    summary.py         # SummaryResponse, SummaryPage

frontend/src/
  api/client.ts        # Axios instance + typed endpoint wrappers
  stores/summaries.ts  # Pinia store: list, delete, upload actions
  style.css            # @layer components — reusable utility classes
  components/
    ConfirmModal.vue   # teleported confirm dialog (replaces window.confirm)
    FileUpload.vue     # drag-and-drop uploader with toast notifications
```

## Conventions

- Python 3.11+ syntax — use `X | Y` unions, `match` where appropriate
- All DB access must be async — no sync SQLAlchemy calls
- Pydantic v2 schema syntax (`model_config`, not `class Config`)
- Use `FastAPI Depends()` for injection — no new module-level singletons
- The Anthropic client lives only in `core/summarizer.py` — do not create a second instance
