"""
Tests de integración para la API de Análisis — endpoints /api/v1/analysis.

W-3: endpoints de ScrapedSource (POST/GET/DELETE /sources).
W-4: endpoints de jobs/results y approve/reject.

Patrón: override_get_db + ASGITransport sobre una app que incluye
el router de análisis (el wiring en main.py llega en W-4).
"""

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.analysis import router as analysis_router
from app.core.database import get_db
from app.services.analysis import url_guard


@pytest.fixture
def override_get_db(db_session):
    async def _get_db_override():
        yield db_session

    return _get_db_override


@pytest.fixture(autouse=True)
def _no_real_dns(monkeypatch):
    """Keep API tests network-free: fake resolver always returns a public IP.

    Literal private IPs (loopback/link-local/metadata) are rejected by the
    guard before any resolution happens, so this patch only affects
    hostname-based URLs used by the CRUD tests (201/409/200/204/404).
    """

    monkeypatch.setattr(url_guard, "_resolve_host", lambda host: ["93.184.216.34"])
    yield


@pytest.fixture
async def client(override_get_db):
    app = FastAPI()
    app.include_router(analysis_router)
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


class TestScrapedSourcesAPI:
    """Endpoints /api/v1/analysis/sources (W-3)."""

    @pytest.mark.asyncio
    async def test_create_source_201(self, client):
        payload = {
            "url": "https://competidor.com/products",
            "name": "Competidor Principal",
            "schedule_interval_minutes": 60,
        }
        response = await client.post("/api/v1/analysis/sources", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["url"] == "https://competidor.com/products"
        assert data["name"] == "Competidor Principal"
        assert data["schedule_interval_minutes"] == 60
        assert data["is_active"] is True
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_source_409_duplicate_url(self, client):
        payload = {"url": "https://duplicada.com"}
        first = await client.post("/api/v1/analysis/sources", json=payload)
        assert first.status_code == 201
        second = await client.post("/api/v1/analysis/sources", json=payload)
        assert second.status_code == 409

    @pytest.mark.asyncio
    async def test_create_source_409_url_reused_after_soft_delete(self, client):
        """Tras soft-delete la url sigue reservada por la UNIQUE del modelo."""
        payload = {"url": "https://reusada.com"}
        created = await client.post("/api/v1/analysis/sources", json=payload)
        assert created.status_code == 201
        source_id = created.json()["id"]

        deleted = await client.delete(f"/api/v1/analysis/sources/{source_id}")
        assert deleted.status_code == 204

        again = await client.post("/api/v1/analysis/sources", json=payload)
        assert again.status_code == 409

    @pytest.mark.asyncio
    async def test_create_source_422_invalid_url(self, client):
        response = await client.post("/api/v1/analysis/sources", json={"url": ""})
        assert response.status_code == 422

    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/admin",
            "http://127.0.0.1:8080/",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]/",
            "http://10.0.0.5/internal",
            "http://192.168.1.10/",
        ],
    )
    @pytest.mark.asyncio
    async def test_create_source_400_private_loopback_url(self, client, url):
        """SSRF guard (D7): private/loopback/link-local/metadata URLs are rejected."""
        response = await client.post("/api/v1/analysis/sources", json={"url": url})
        assert response.status_code == 400

    @pytest.mark.parametrize("url", ["ftp://example.com/file", "file:///etc/passwd"])
    @pytest.mark.asyncio
    async def test_create_source_400_non_http_scheme(self, client, url):
        """SSRF guard (D7): only http/https schemes are accepted."""
        response = await client.post("/api/v1/analysis/sources", json={"url": url})
        assert response.status_code == 400

    @pytest.mark.parametrize("url", ["http://example.com/", "https://example.com/products"])
    @pytest.mark.asyncio
    async def test_create_source_201_public_url(self, client, url):
        """SSRF guard (D7): valid public http/https URLs still create the source."""
        response = await client.post("/api/v1/analysis/sources", json={"url": url})
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_list_sources_paginated(self, client):
        for i in range(5):
            created = await client.post(
                "/api/v1/analysis/sources", json={"url": f"https://s{i}.com"}
            )
            assert created.status_code == 201

        response = await client.get("/api/v1/analysis/sources?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_list_sources_excludes_soft_deleted(self, client):
        created = await client.post(
            "/api/v1/analysis/sources", json={"url": "https://viva.com"}
        )
        source_id = created.json()["id"]
        await client.delete(f"/api/v1/analysis/sources/{source_id}")

        response = await client.get("/api/v1/analysis/sources")
        assert response.status_code == 200
        assert all(item["id"] != source_id for item in response.json()["items"])

    @pytest.mark.asyncio
    async def test_delete_source_204(self, client):
        created = await client.post(
            "/api/v1/analysis/sources", json={"url": "https://delete.me"}
        )
        source_id = created.json()["id"]

        response = await client.delete(f"/api/v1/analysis/sources/{source_id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_source_404_unknown(self, client):
        response = await client.delete(f"/api/v1/analysis/sources/{uuid.uuid4()}")
        assert response.status_code == 404
