# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

DocSummarizer watches a local folder for PDF/DOCX/TXT/MD files, summarizes them with Claude (Anthropic API), stores results in SQLite, and serves them through a FastAPI REST API and a Vue 3 web UI.

## Commands

All backend commands must be run from the `backend/` directory (settings reads `.env` relative to CWD).

```bash
# Backend — install deps (generates uv.lock on first run)
cd backend && uv sync

# Run the API server (dev)
uv run doc-summarizer serve --reload

# Run the file watcher
uv run doc-summarizer watch ./data/watch

# Summarize a single file on demand
uv run doc-summarizer summarize path/to/file.pdf

# Lint
uv run ruff check src/
uv run ruff format src/

# Run all tests
uv run pytest

# Run a single test file
uv run pytest src/tests/test_api.py

# Run a single test by name
uv run pytest src/tests/test_api.py::test_health_check
```

```bash
# Frontend — install deps (generates package-lock.json on first run)
cd frontend && npm install

# Dev server (proxies /api → localhost:8000)
npm run dev

# Type-check
npm run type-check

# Production build
npm run build
```

**Important:** Tests require `ANTHROPIC_API_KEY` to be set (even for the health check) because `config.py` instantiates `Settings()` at module import time and `anthropic_api_key` has no default. Run tests as:
```bash
ANTHROPIC_API_KEY=sk-ant-... uv run pytest
```

## Architecture

### Backend request flow

```
HTTP request
  → FastAPI route (api/routes/*.py)
  → SummaryRepository (db/repository.py)   ← AsyncSession via Depends(get_db)
  → SQLAlchemy async / aiosqlite
  → api/utils.to_response()                ← converts ORM → Pydantic
  → JSON response
```

Upload pipeline specifically:
```
POST /api/summaries/upload
  → validate extension
  → SHA-256 hash → check for duplicate in DB (return cached if found)
  → write bytes to NamedTemporaryFile
  → core/parser.py dispatch → parser (pdf/docx/text)
  → delete tempfile
  → core/summarizer.summarize_document() [SYNCHRONOUS — blocks event loop]
  → persist Summary ORM model
  → to_response()
```

### Key architectural facts

**`key_topics` is stored as a JSON string**, not a native array. The `Summary` ORM model has `key_topics: Mapped[str]`. Always use `json.dumps(list)` when writing and `json.loads(str)` when reading. `api/utils.to_response()` handles this for all routes — add new routes through that helper, not inline.

**`settings` is a module-level singleton** instantiated at import in `config.py`. All env vars are read once at startup from a `.env` file in the CWD. Running commands from the wrong directory silently uses wrong paths.

**`summarize_document()` is synchronous** (the Anthropic SDK call in `core/summarizer.py` is not awaited). It blocks the event loop during summarization — this is a known issue to address.

**`SummaryRepository.get_all()` counts inefficiently** — it runs a second full-table `SELECT` just to count rows. Use `func.count()` subquery when fixing.

**`@app.on_event("startup")` is deprecated** in FastAPI 0.115+. Needs migration to the `lifespan` context manager pattern (tracked in TASKS.md).

### Frontend architecture

The Vite dev server proxies all `/api` requests to `localhost:8000` (`vite.config.ts`), so no `VITE_API_BASE_URL` is needed in dev. All API calls go through `src/api/client.ts` (typed Axios wrappers). State lives in `src/stores/summaries.ts` (Pinia). Views own their own local loading/error state for detail and search; the Pinia store owns list state.

**Tailwind utility classes** for this project (`.card`, `.btn-primary`, `.btn-ghost`, `.badge`, `.input`) are defined under `@layer components` in `src/style.css` — prefer those over ad-hoc inline Tailwind classes.

The `@/` import alias maps to `frontend/src/`.

### File structure summary

```
backend/src/doc_summarizer/
  config.py          # pydantic-settings singleton (Settings)
  main.py            # FastAPI app + middleware + router registration
  cli.py             # click CLI: serve / watch / summarize
  api/
    utils.py         # to_response() — single place that converts ORM → schema
    routes/          # one file per resource; all use Depends(get_db)
  core/
    summarizer.py    # Anthropic API call (sync); returns dict with 3 keys
    parser.py        # dispatch by extension → parsers/
    watcher.py       # watchdog Observer wrapper
  db/
    models.py        # Summary ORM model (key_topics stored as JSON string)
    session.py       # engine, async_session_factory, init_db()
    repository.py    # SummaryRepository — all DB access here
  schemas/
    summary.py       # SummaryResponse, SummaryPage, SummaryCreate

frontend/src/
  api/client.ts      # Axios instance + typed wrappers for every endpoint
  stores/summaries.ts # Pinia store: list state, delete, upload
  style.css          # @layer components — reusable utility classes
```

## Known Issues / Next Up

See `TASKS.md` for the full prioritized list. The top items are:

1. Commit `uv.lock` and `package-lock.json` (lock files don't exist yet)
2. Migrate `@app.on_event("startup")` → `lifespan` in `main.py`
3. Add retry/backoff to `summarizer.py` for rate limit errors
4. Add rotating file log handler
5. Fix inefficient `COUNT` in `SummaryRepository.get_all()`
