"""
Tests para PixelRAGService — verifica wrapper de renderizado.

Sigue TDD: estos tests describen el comportamiento esperado
del servicio PixelRAG antes de su implementación.
"""

import pytest


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
