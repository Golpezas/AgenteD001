"""
Tests para PixelRAGService — verifica wrapper de renderizado.

Sigue TDD: estos tests describen el comportamiento esperado
del servicio PixelRAG antes de su implementación.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.analysis.pipeline_state as ps_module
from app.core.database import get_db
from app.main import create_app


class TestPixelRAGService:
    """Suite de tests para PixelRAGService."""

    @pytest.mark.asyncio
    async def test_service_can_be_imported(self):
        """Debe poder importar el servicio."""
        from app.services.pixelrag import PixelRAGService  # noqa: F401
        assert True

    @pytest.mark.asyncio
    async def test_render_url_rejects_empty_string(self):
        """Debe lanzar ValueError para URL vacía."""
        from app.services.pixelrag import PixelRAGService

        service = PixelRAGService()
        with pytest.raises(ValueError, match="URL cannot be empty"):
            await service.render_url("")

    @pytest.mark.asyncio
    async def test_render_url_rejects_invalid_url(self):
        """Debe lanzar ValueError para URL inválida."""
        from app.services.pixelrag import PixelRAGService

        service = PixelRAGService()
        with pytest.raises(ValueError, match="Invalid URL format"):
            await service.render_url("not-a-url")

    @pytest.mark.asyncio
    async def test_health_status(self):
        """Debe retornar estado del servicio."""
        from app.services.pixelrag import PixelRAGService

        service = PixelRAGService()
        status = await service.health()
        assert isinstance(status, dict)
        assert "status" in status


@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Reemplaza la dependencia get_db con la sesión de test."""

    async def _get_db_override():
        yield db_session

    return _get_db_override


@pytest.fixture
async def client(override_get_db):
    """Cliente HTTP asíncrono contra la app real."""
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_pipeline_state():
    """Evita contaminación del singleton pipeline_state entre tests."""
    ps_module.pipeline_state.active = False
    ps_module.pipeline_state.last_successful_run = None
    yield
    ps_module.pipeline_state.active = False
    ps_module.pipeline_state.last_successful_run = None


class TestPixelRAGHealthEndpoint:
    """Tests del endpoint GET /api/v1/pixelrag/test (R-X03)."""

    @pytest.mark.asyncio
    async def test_health_200_with_pipeline_block(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """Con pipeline registrado, la respuesta DEBE incluir analysis_pipeline."""
        ps_module.pipeline_state.mark_active()

        response = await client.get("/api/v1/pixelrag/test")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "pixelrag"
        assert data["status"] == "available"
        pipeline = data["analysis_pipeline"]
        assert pipeline["active"] is True
        assert pipeline["last_successful_run"] is None
        assert pipeline["pending_jobs"] == 0

    @pytest.mark.asyncio
    async def test_health_200_without_pipeline_block(self, client: AsyncClient):
        """Sin pipeline registrado, NO debe incluir analysis_pipeline."""
        response = await client.get("/api/v1/pixelrag/test")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "pixelrag"
        assert "analysis_pipeline" not in data

    @pytest.mark.asyncio
    async def test_health_404_in_production(
        self, client: AsyncClient, monkeypatch,
    ):
        """En producción, el endpoint NO debe estar disponible (404)."""
        from app.core.config import settings

        monkeypatch.setattr(settings, "environment", "production")

        response = await client.get("/api/v1/pixelrag/test")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_health_500_on_service_error(self, client: AsyncClient):
        """Error del servicio PixelRAG DEBE propagarse como 500."""
        with patch("app.services.pixelrag.PixelRAGService") as mock_service:
            mock_service.return_value.health = AsyncMock(
                side_effect=Exception("render broken")
            )

            response = await client.get("/api/v1/pixelrag/test")

        assert response.status_code == 500
        assert "PixelRAG error" in response.json()["detail"]
