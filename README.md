<div align="center">

# 📄 DocSummarizer

**Drop a document. Get an instant AI summary.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue-3-4FC08D?style=flat-square&logo=vue.js&logoColor=white)](https://vuejs.org)
[![Anthropic](https://img.shields.io/badge/Powered%20by-Claude-D97706?style=flat-square)](https://anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-6366f1?style=flat-square)](LICENSE)

</div>

---

DocSummarizer watches a local folder for new documents and automatically summarizes them using [Claude](https://anthropic.com). Summaries are stored in a searchable SQLite database and displayed through a sleek dark-mode web UI.

## ✨ Features

- **Auto-watch** — drop a PDF, DOCX, TXT, or Markdown file into the watch folder and it's summarized within seconds
- **Structured summaries** — get a short (2-3 sentence) summary, a full paragraph summary, and key topic tags for every document
- **Duplicate detection** — SHA-256 content hashing means unchanged files are never re-summarized
- **Full-text search** — find any document by content, filename, or topic
- **Manual upload** — drag-and-drop upload via the web UI as an alternative to folder watching
- **REST API** — clean FastAPI backend with OpenAPI docs at `/docs`
- **Dark mode UI** — Vue 3 frontend with Tailwind CSS, built for readability

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| AI | Anthropic Python SDK (Claude) |
| Database | SQLite + SQLAlchemy 2.x (async) |
| File Watching | Watchdog |
| Document Parsing | pypdf, python-docx |
| Frontend | Vue 3, Vite, TypeScript, Pinia |
| Styling | Tailwind CSS |
| Package Manager | uv |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 20+ and npm
- An [Anthropic API key](https://console.anthropic.com/)

### 1 — Backend

```bash
cd backend

# Install dependencies
uv sync

# Copy and fill in your config
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# Start the API server
uv run doc-summarizer serve
```

The API will be running at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 2 — Frontend

```bash
cd frontend

npm install
npm run dev
```

The UI will be running at `http://localhost:5173`.

### 3 — Watch a folder

In a separate terminal:

```bash
cd backend
uv run doc-summarizer watch ./data/watch
```

Any PDF, DOCX, TXT, or MD file placed in that folder will be automatically parsed and summarized.

## ⚙️ Configuration

All backend configuration is via environment variables (`.env` file):

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | **required** | Your Anthropic API key |
| `WATCH_FOLDER` | `./data/watch` | Folder to monitor for new documents |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/summaries.db` | SQLite database path |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`) |
| `API_HOST` | `0.0.0.0` | Host to bind the API server |
| `API_PORT` | `8000` | Port to bind the API server |

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/summaries` | List all summaries (paginated) |
| `GET` | `/api/summaries/{id}` | Get a single summary |
| `DELETE` | `/api/summaries/{id}` | Delete a summary |
| `POST` | `/api/summaries/upload` | Upload and summarize a file |
| `GET` | `/api/search?q=...` | Search summaries by content |

Full interactive docs are available at `http://localhost:8000/docs` when the server is running.

## 🗂 Project Structure

```
doc-summarizer/
├── backend/
│   ├── src/
│   │   ├── doc_summarizer/
│   │   │   ├── main.py          # FastAPI app entry point
│   │   │   ├── config.py        # Pydantic settings
│   │   │   ├── cli.py           # Click CLI
│   │   │   ├── api/routes/      # REST endpoints
│   │   │   ├── core/            # Watcher, parsers, summarizer
│   │   │   ├── db/              # SQLAlchemy models & repository
│   │   │   └── schemas/         # Pydantic request/response models
│   │   └── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── views/               # SummaryList, SummaryDetail, Search
│   │   ├── components/          # SummaryCard, SearchBar, FileUpload
│   │   ├── stores/              # Pinia state
│   │   └── api/                 # Axios client + TypeScript types
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 🧪 Running Tests

```bash
cd backend
uv run pytest
```

## 📋 Roadmap

- [ ] SQLite FTS5 full-text search
- [ ] Tag-based filtering
- [ ] Export summaries to Markdown or PDF
- [ ] Batch re-summarization with custom prompts
- [ ] "Ask a question" mode using RAG over stored summaries
- [ ] Docker Compose for one-command deployment
- [ ] OCR support for image-based PDFs

## 📝 License

[MIT](LICENSE) — Matthew Wilson, 2026
