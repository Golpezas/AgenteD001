"""
Tests de integración para la API de Análisis — endpoints /api/v1/analysis.

W-3: endpoints de ScrapedSource (POST/GET/DELETE /sources).
W-4: jobs/results y approve/reject + BackgroundTasks con session factory
     inyectable y build_orchestrator mockeable + wiring del router en main.py.

Patrón: override_get_db + ASGITransport sobre create_app(). Las bg tasks
completan antes de que retorne client.post (ASGITransport) → determinista.
"""

import base64
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.analysis import MAX_IMAGE_BYTES_BASE64, MAX_URL_CHARS
from app.core.database import get_db
from app.services.analysis import url_guard
from app.main import create_app


class _FakeSessionFactory:
    """Async CM que devuelve siempre la misma sesión (inyección en tests)."""

    def __init__(self, session):
        self._session = session

    def __call__(self):
        return self

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *exc):
        return False


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
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def fake_session_factory(monkeypatch, db_session):
    """Inyecta la session factory de módulo usada por _process_job_task."""
    import app.api.analysis as analysis_api

    factory = _FakeSessionFactory(db_session)
    monkeypatch.setattr(analysis_api, "async_session", factory)
    return factory


@pytest.fixture
def mock_build_orchestrator(monkeypatch):
    """Mockea build_orchestrator para tests de wiring (sin pipeline real)."""
    import app.api.analysis as analysis_api
    from app.services.analysis.orchestrator import AnalysisOrchestrator

    mock_orch = AsyncMock(spec=AnalysisOrchestrator)
    mock_orch.process_job.return_value = None
    mock_orch.get_job_status.return_value = {
        "job_id": str(uuid.uuid4()),
        "status": "pending",
        "job_type": "image",
        "error_message": None,
        "result": None,
    }
    mock_orch.approve_proposal.return_value = True
    mock_orch.reject_proposal.return_value = True

    monkeypatch.setattr(
        analysis_api, "build_orchestrator", MagicMock(return_value=mock_orch)
    )
    return mock_orch


@pytest.fixture
def mock_pipeline_services(monkeypatch):
    """Reemplaza los servicios reales del pipeline por fakes (sin red real).

    Se parchean los nombres del módulo api.analysis (sitio de construcción
    de build_orchestrator); el orchestrator solo usa las instancias.
    """
    import app.api.analysis as analysis_api
    from app.schemas.analysis import AnalysisProposal

    class FakeGemini:
        def __init__(self, *args, **kwargs):
            self.analyze_image = AsyncMock(
                return_value=AnalysisProposal(
                    product_name="Producto Mock",
                    extracted_price=199.99,
                    confidence_score=0.91,
                    raw_data={"source": "fake-gemini"},
                )
            )
            self.analyze_scraped_content = AsyncMock(
                return_value=AnalysisProposal(
                    product_name="Producto Mock URL",
                    extracted_price=99.5,
                    confidence_score=0.8,
                    raw_data={"source": "fake-gemini-url"},
                )
            )

    class FakeScraper:
        def __init__(self, *args, **kwargs):
            self.scrape = AsyncMock()

    class FakePixelRAG:
        def __init__(self, *args, **kwargs):
            self.capture_for_analysis = AsyncMock(
                side_effect=RuntimeError("no screenshot in tests")
            )

    class FakeNotifications:
        def __init__(self, *args, **kwargs):
            self.create_notification = AsyncMock(return_value=None)

    monkeypatch.setattr(analysis_api, "GeminiClient", FakeGemini)
    monkeypatch.setattr(analysis_api, "WebScraper", FakeScraper)
    monkeypatch.setattr(analysis_api, "PixelRAGService", FakePixelRAG)
    monkeypatch.setattr(analysis_api, "NotificationService", FakeNotifications)


def _image_payload() -> dict:
    return {
        "job_type": "image",
        "input_data": {
            "image_bytes": base64.b64encode(b"fake-jpeg-bytes").decode()
        },
    }


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


class TestAnalysisJobsAPI:
    """Endpoints de jobs: POST/GET /jobs, GET /jobs/{id}, GET /results (W-4)."""

    @pytest.mark.asyncio
    async def test_create_image_job_202(
        self, client, fake_session_factory, mock_build_orchestrator
    ):
        response = await client.post("/api/v1/analysis/jobs", json=_image_payload())
        assert response.status_code == 202
        data = response.json()
        assert data["job_type"] == "image"
        assert data["status"] == "pending"
        stored_b64 = data["input_data"]["image_bytes"]
        assert base64.b64decode(stored_b64) == b"fake-jpeg-bytes"
        assert "id" in data

        # La bg task se ejecutó con el orchestrator mockeado
        mock_build_orchestrator.process_job.assert_awaited_once_with(
            uuid.UUID(data["id"])
        )

    @pytest.mark.asyncio
    async def test_create_url_job_202(
        self, client, fake_session_factory, mock_build_orchestrator
    ):
        payload = {"job_type": "url", "input_data": {"url": "https://example.com"}}
        response = await client.post("/api/v1/analysis/jobs", json=payload)
        assert response.status_code == 202
        assert response.json()["job_type"] == "url"

    @pytest.mark.asyncio
    async def test_create_job_400_invalid_job_type(
        self, client, fake_session_factory, mock_build_orchestrator
    ):
        payload = {"job_type": "video", "input_data": {"url": "https://x.com"}}
        response = await client.post("/api/v1/analysis/jobs", json=payload)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_image_job_400_missing_image_bytes(
        self, client, fake_session_factory, mock_build_orchestrator
    ):
        payload = {"job_type": "image", "input_data": {}}
        response = await client.post("/api/v1/analysis/jobs", json=payload)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_url_job_400_missing_url(
        self, client, fake_session_factory, mock_build_orchestrator
    ):
        payload = {"job_type": "url", "input_data": {}}
        response = await client.post("/api/v1/analysis/jobs", json=payload)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_job_422_missing_job_type(
        self, client, fake_session_factory, mock_build_orchestrator
    ):
        response = await client.post(
            "/api/v1/analysis/jobs", json={"input_data": {}}
        )
        assert response.status_code == 422

    # ── D7/R1-001: url jobs must pass the SSRF guard; D4: size limits ──────

    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/admin",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]/",
            "http://10.0.0.1/internal",
            "http://192.168.1.1/",
        ],
    )
    @pytest.mark.asyncio
    async def test_create_url_job_400_private_loopback_url(
        self, client, fake_session_factory, mock_build_orchestrator, url
    ):
        """SSRF guard (D7): private/loopback/link-local URLs are rejected (400)."""
        payload = {"job_type": "url", "input_data": {"url": url}}
        response = await client.post("/api/v1/analysis/jobs", json=payload)
        assert response.status_code == 400
        mock_build_orchestrator.process_job.assert_not_awaited()

    @pytest.mark.parametrize("url", ["ftp://example.com/file", "file:///etc/passwd"])
    @pytest.mark.asyncio
    async def test_create_url_job_400_non_http_scheme(
        self, client, fake_session_factory, mock_build_orchestrator, url
    ):
        """SSRF guard (D7): only http/https schemes are accepted (400)."""
        payload = {"job_type": "url", "input_data": {"url": url}}
        response = await client.post("/api/v1/analysis/jobs", json=payload)
        assert response.status_code == 400
        mock_build_orchestrator.process_job.assert_not_awaited()

    @pytest.mark.parametrize(
        "url", ["http://example.com/", "https://example.com/products"]
    )
    @pytest.mark.asyncio
    async def test_create_url_job_202_public_url(
        self, client, fake_session_factory, mock_build_orchestrator, url
    ):
        """SSRF guard (D7): public http/https URLs still schedule the job (202)."""
        payload = {"job_type": "url", "input_data": {"url": url}}
        response = await client.post("/api/v1/analysis/jobs", json=payload)
        assert response.status_code == 202
        assert response.json()["job_type"] == "url"

    @pytest.mark.asyncio
    async def test_create_url_job_400_url_too_long(
        self, client, fake_session_factory, mock_build_orchestrator
    ):
        """D4: input_data.url longer than 2048 chars is rejected (400)."""
        payload = {
            "job_type": "url",
            "input_data": {"url": "https://example.com/" + "a" * MAX_URL_CHARS},
        }
        response = await client.post("/api/v1/analysis/jobs", json=payload)
        assert response.status_code == 400
        mock_build_orchestrator.process_job.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_image_job_413_image_bytes_too_large(
        self, client, fake_session_factory, mock_build_orchestrator
    ):
        """D4: image_bytes base64 payload over 8 MiB is rejected (413)."""
        payload = {
            "job_type": "image",
            "input_data": {"image_bytes": "A" * (MAX_IMAGE_BYTES_BASE64 + 1)},
        }
        response = await client.post("/api/v1/analysis/jobs", json=payload)
        assert response.status_code == 413
        mock_build_orchestrator.process_job.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_jobs_paginated(
        self, client, fake_session_factory, mock_build_orchestrator
    ):
        for _ in range(3):
            await client.post("/api/v1/analysis/jobs", json=_image_payload())

        response = await client.get("/api/v1/analysis/jobs?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_get_jobs_filter_by_status(
        self, client, fake_session_factory, mock_build_orchestrator
    ):
        await client.post("/api/v1/analysis/jobs", json=_image_payload())

        response = await client.get("/api/v1/analysis/jobs?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert all(j["status"] == "pending" for j in data["items"])

    @pytest.mark.asyncio
    async def test_get_job_by_id_200(
        self, client, fake_session_factory, mock_build_orchestrator
    ):
        created = await client.post("/api/v1/analysis/jobs", json=_image_payload())
        job_id = created.json()["id"]
        mock_build_orchestrator.get_job_status.return_value = {
            "job_id": job_id,
            "status": "pending",
            "job_type": "image",
            "error_message": None,
            "result": None,
        }

        response = await client.get(f"/api/v1/analysis/jobs/{job_id}")
        assert response.status_code == 200
        assert response.json()["job_id"] == job_id

    @pytest.mark.asyncio
    async def test_get_job_by_id_404(
        self, client, fake_session_factory, mock_build_orchestrator
    ):
        mock_build_orchestrator.get_job_status.return_value = None
        response = await client.get(f"/api/v1/analysis/jobs/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_results_empty(
        self, client, fake_session_factory, mock_build_orchestrator
    ):
        response = await client.get("/api/v1/analysis/results")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []


class TestApproveRejectAPI:
    """Approve/reject: 200 con transición; 404 inexistente; 409 ya resuelto (W-4)."""

    @pytest.fixture
    async def proposal_result(self, db_session):
        from app.repositories.analysis import (
            AnalysisJobRepository,
            AnalysisResultRepository,
        )

        job = await AnalysisJobRepository(db_session).create(
            {
                "job_type": "image",
                "input_data": {"image_bytes": "eA=="},
                "status": "completed",
            }
        )
        result = await AnalysisResultRepository(db_session).create(
            {
                "job_id": job.id,
                "status": "proposal",
                "product_name": "Producto Propuesto",
                "extracted_price": 123.45,
                "confidence_score": 0.9,
            }
        )
        return result

    @pytest.mark.asyncio
    async def test_approve_result_200(
        self, client, proposal_result, mock_build_orchestrator
    ):
        response = await client.post(
            f"/api/v1/analysis/results/{proposal_result.id}/approve"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(proposal_result.id)
        assert data["status"] == "accepted"
        mock_build_orchestrator.approve_proposal.assert_awaited_once_with(
            proposal_result.id
        )

    @pytest.mark.asyncio
    async def test_reject_result_200_with_reason(
        self, client, proposal_result, mock_build_orchestrator
    ):
        response = await client.post(
            f"/api/v1/analysis/results/{proposal_result.id}/reject",
            json={"reason": "precio inflado"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(proposal_result.id)
        assert data["status"] == "rejected"
        assert data["reason"] == "precio inflado"
        mock_build_orchestrator.reject_proposal.assert_awaited_once_with(
            proposal_result.id, "precio inflado"
        )

    @pytest.mark.asyncio
    async def test_reject_result_200_without_reason(
        self, client, proposal_result, mock_build_orchestrator
    ):
        response = await client.post(
            f"/api/v1/analysis/results/{proposal_result.id}/reject"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["reason"] is None

    @pytest.mark.asyncio
    async def test_approve_result_404(
        self, client, mock_build_orchestrator
    ):
        response = await client.post(
            f"/api/v1/analysis/results/{uuid.uuid4()}/approve"
        )
        assert response.status_code == 404
        mock_build_orchestrator.approve_proposal.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_reject_result_404(
        self, client, mock_build_orchestrator
    ):
        response = await client.post(
            f"/api/v1/analysis/results/{uuid.uuid4()}/reject", json={}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_approve_result_409_already_accepted(
        self, client, db_session, mock_build_orchestrator
    ):
        from app.models.analysis import AnalysisResult
        from app.repositories.analysis import (
            AnalysisJobRepository,
            AnalysisResultRepository,
        )

        job = await AnalysisJobRepository(db_session).create(
            {
                "job_type": "image",
                "input_data": {"image_bytes": "eA=="},
                "status": "completed",
            }
        )
        accepted = await AnalysisResultRepository(db_session).create(
            {
                "job_id": job.id,
                "status": "accepted",
                "product_name": "Ya Aceptado",
            }
        )

        response = await client.post(
            f"/api/v1/analysis/results/{accepted.id}/approve"
        )
        assert response.status_code == 409
        mock_build_orchestrator.approve_proposal.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_reject_result_409_already_rejected(
        self, client, db_session, mock_build_orchestrator
    ):
        from app.repositories.analysis import (
            AnalysisJobRepository,
            AnalysisResultRepository,
        )

        job = await AnalysisJobRepository(db_session).create(
            {
                "job_type": "image",
                "input_data": {"image_bytes": "eA=="},
                "status": "completed",
            }
        )
        rejected = await AnalysisResultRepository(db_session).create(
            {
                "job_id": job.id,
                "status": "rejected",
                "product_name": "Ya Rechazado",
            }
        )

        response = await client.post(
            f"/api/v1/analysis/results/{rejected.id}/reject", json={}
        )
        assert response.status_code == 409
        mock_build_orchestrator.reject_proposal.assert_not_awaited()


class TestJobsPipelineIntegration:
    """1 test de pipeline real con servicios mockeados (sin red), vía bg task (W-4)."""

    @pytest.mark.asyncio
    async def test_create_job_runs_pipeline_in_background(
        self, client, fake_session_factory, mock_pipeline_services
    ):
        response = await client.post("/api/v1/analysis/jobs", json=_image_payload())
        assert response.status_code == 202
        job = response.json()
        assert job["status"] == "pending"

        # La bg task completa antes de que retorne client.post (ASGITransport)
        results = await client.get("/api/v1/analysis/results")
        assert results.status_code == 200
        items = results.json()["items"]
        assert len(items) == 1
        assert items[0]["status"] == "proposal"
        assert items[0]["product_name"] == "Producto Mock"
        assert items[0]["extracted_price"] == 199.99

        job_detail = await client.get(f"/api/v1/analysis/jobs/{job['id']}")
        assert job_detail.status_code == 200
        assert job_detail.json()["status"] == "completed"
        assert job_detail.json()["result"] is not None
