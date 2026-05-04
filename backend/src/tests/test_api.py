import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health_check():
    from doc_summarizer.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
