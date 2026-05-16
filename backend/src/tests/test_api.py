"""API integration tests — in-memory SQLite DB, Anthropic client mocked."""

from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from doc_summarizer.db.models import Base
from doc_summarizer.main import app
from doc_summarizer.api.dependencies import get_db

# ── Fixtures ──────────────────────────────────────────────────────────────────

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async test client backed by a fresh in-memory SQLite database."""
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    await engine.dispose()


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        response = await c.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Summaries list ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_summaries_empty(client: AsyncClient):
    response = await client.get("/api/summaries")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1


# ── Get by ID ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_summary_not_found(client: AsyncClient):
    response = await client.get("/api/summaries/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Summary not found"


# ── Upload ───────────────────────────────────────────────────────────────────

_MOCK_API_RESPONSE = (
    '{"summary_short":"A short test summary.",'
    '"summary_long":"A longer paragraph summary for testing purposes.",'
    '"key_topics":["testing","mocks","fastapi"]}'
)


@pytest.mark.asyncio
async def test_upload_txt_file(client: AsyncClient):
    """Upload a plain-text file with the Anthropic call mocked out."""
    content = b"This is test document content for summarization."

    with patch("doc_summarizer.core.summarizer._call_api", return_value=_MOCK_API_RESPONSE):
        response = await client.post(
            "/api/summaries/upload",
            files={"file": ("test.txt", content, "text/plain")},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["file_name"] == "test.txt"
    assert data["file_type"] == "txt"
    assert data["summary_short"] == "A short test summary."
    assert data["key_topics"] == ["testing", "mocks", "fastapi"]
    assert "id" in data


@pytest.mark.asyncio
async def test_upload_unsupported_type(client: AsyncClient):
    response = await client.post(
        "/api/summaries/upload",
        files={"file": ("report.xlsx", b"data", "application/octet-stream")},
    )
    assert response.status_code == 422
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_duplicate_returns_cached(client: AsyncClient):
    """Uploading identical content twice returns the cached summary without re-calling Claude."""
    content = b"Unique document content that will be hashed for dedup testing."
    call_count = 0

    def counting_mock(text: str) -> str:
        nonlocal call_count
        call_count += 1
        return '{"summary_short":"Short.","summary_long":"Long.","key_topics":["dup"]}'

    with patch("doc_summarizer.core.summarizer._call_api", side_effect=counting_mock):
        r1 = await client.post(
            "/api/summaries/upload",
            files={"file": ("doc.txt", content, "text/plain")},
        )
        r2 = await client.post(
            "/api/summaries/upload",
            files={"file": ("doc.txt", content, "text/plain")},
        )

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"], "Second upload should return the cached summary"
    assert call_count == 1, "Claude should only have been called once"


# ── Delete ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_summary(client: AsyncClient):
    with patch("doc_summarizer.core.summarizer._call_api", return_value='{"summary_short":"S.","summary_long":"L.","key_topics":[]}'):
        upload = await client.post(
            "/api/summaries/upload",
            files={"file": ("todelete.txt", b"delete me please", "text/plain")},
        )
    assert upload.status_code == 201
    summary_id = upload.json()["id"]

    delete_resp = await client.delete(f"/api/summaries/{summary_id}")
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/api/summaries/{summary_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_summary(client: AsyncClient):
    response = await client.delete("/api/summaries/999")
    assert response.status_code == 404
