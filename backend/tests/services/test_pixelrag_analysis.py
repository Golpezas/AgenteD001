"""
Tests para PixelRAGService.capture_for_analysis — spec R-X04 (ScreenshotResult).
"""

import os
import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from PIL import Image

from app.schemas.analysis import ScreenshotResult


@pytest.fixture
def valid_png_bytes():
    """Bytes PNG válidos (>1KB) para simular el render del engine."""
    # Ruido aleatorio 40x40: incompresible, garantiza PNG >1KB (spec R-X04)
    img = Image.frombytes("RGB", (40, 40), os.urandom(40 * 40 * 3))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestPixelRAGCaptureForAnalysis:
    """Tests del método capture_for_analysis en PixelRAGService."""

    @pytest.fixture
    def pixelrag_service(self):
        from app.services.pixelrag import PixelRAGService

        service = PixelRAGService()
        # Pre-configurar para evitar lazy init real
        service._engine = MagicMock()
        service._initialized = True
        return service

    @pytest.mark.asyncio
    async def test_capture_for_analysis_calls_render_url(self, pixelrag_service, valid_png_bytes):
        """capture_for_analysis debe delegar a render_url y retornar ScreenshotResult."""
        mock_engine = MagicMock()
        mock_engine.render_url = AsyncMock(return_value=valid_png_bytes)
        pixelrag_service._engine = mock_engine

        result = await pixelrag_service.capture_for_analysis("https://example.com/product")

        assert isinstance(result, ScreenshotResult)
        assert result.image_bytes == valid_png_bytes
        assert result.url == "https://example.com/product"
        assert isinstance(result.timestamp, datetime)
        assert result.resolution == (40, 40)
        mock_engine.render_url.assert_called_once_with("https://example.com/product")

    @pytest.mark.asyncio
    async def test_capture_for_analysis_validates_url(self, pixelrag_service):
        """capture_for_analysis debe validar la URL antes de llamar a render."""
        with patch.object(pixelrag_service, "render_url", new_callable=AsyncMock) as mock_render:
            mock_render.return_value = b"fake_png_bytes"

            # URL vacía
            with pytest.raises(ValueError, match="URL cannot be empty"):
                await pixelrag_service.capture_for_analysis("")

            # Solo whitespace
            with pytest.raises(ValueError, match="URL cannot be empty"):
                await pixelrag_service.capture_for_analysis("   ")

            # URL inválida
            with pytest.raises(ValueError, match="Invalid URL format"):
                await pixelrag_service.capture_for_analysis("not-a-url")

            # No debe llamar a render_url si la validación falla
            mock_render.assert_not_called()

    @pytest.mark.asyncio
    async def test_capture_for_analysis_propagates_render_error(self, pixelrag_service):
        """Si render_url falla, capture_for_analysis debe propagar el error (spec R-X04)."""
        mock_engine = MagicMock()
        mock_engine.render_url = AsyncMock(side_effect=Exception("Chromium not available"))
        pixelrag_service._engine = mock_engine

        # Los errores DEBEN propagarse envueltos en RuntimeError, NO retornar None
        with pytest.raises(RuntimeError, match="Render failed"):
            await pixelrag_service.capture_for_analysis("https://example.com/product")
        mock_engine.render_url.assert_called_once_with("https://example.com/product")

    @pytest.mark.asyncio
    async def test_capture_for_analysis_returns_screenshot_result(self, pixelrag_service, valid_png_bytes):
        """capture_for_analysis debe retornar ScreenshotResult con PNG >1KB y metadatos."""
        mock_engine = MagicMock()
        mock_engine.render_url = AsyncMock(return_value=valid_png_bytes)
        pixelrag_service._engine = mock_engine

        result = await pixelrag_service.capture_for_analysis("https://example.com/product")

        assert isinstance(result, ScreenshotResult)
        assert result.image_bytes.startswith(b"\x89PNG")
        assert len(result.image_bytes) > 1024
        assert result.url == "https://example.com/product"
        assert isinstance(result.timestamp, datetime)
        assert result.resolution == (40, 40)
        mock_engine.render_url.assert_called_once_with("https://example.com/product")

    @pytest.mark.asyncio
    async def test_capture_for_analysis_raises_when_no_engine(self, pixelrag_service):
        """capture_for_analysis debe lanzar RuntimeError si PixelRAG no está disponible."""
        pixelrag_service._engine = None
        pixelrag_service._initialized = True

        with pytest.raises(RuntimeError, match="PixelRAG is not available"):
            await pixelrag_service.capture_for_analysis("https://example.com")


class TestPixelRAGServiceHealth:
    """Tests del health check del servicio."""

    @pytest.fixture
    def pixelrag_service(self):
        from app.services.pixelrag import PixelRAGService

        service = PixelRAGService()
        service._engine = MagicMock()
        service._initialized = True
        return service

    @pytest.mark.asyncio
    async def test_health_available_when_engine_loaded(self, pixelrag_service):
        """health() debe retornar available si engine está inicializado."""
        health = await pixelrag_service.health()
        assert health["status"] == "available"

    @pytest.mark.asyncio
    async def test_health_unavailable_when_engine_not_loaded(self, pixelrag_service):
        """health() debe retornar unavailable si engine no se pudo cargar."""
        pixelrag_service._engine = None
        pixelrag_service._initialized = True

        health = await pixelrag_service.health()
        assert health["status"] == "unavailable"

    @pytest.mark.asyncio
    async def test_health_calls_lazy_init(self, pixelrag_service):
        """health() debe llamar a _lazy_init."""
        with patch.object(pixelrag_service, "_lazy_init", new_callable=AsyncMock) as mock_init:
            pixelrag_service._engine = None
            pixelrag_service._initialized = False

            await pixelrag_service.health()
            mock_init.assert_called_once()


class TestPixelRAGServiceRenderUrl:
    """Tests del método render_url existente."""

    @pytest.fixture
    def pixelrag_service(self):
        from app.services.pixelrag import PixelRAGService

        service = PixelRAGService()
        service._engine = MagicMock()
        service._initialized = True
        return service

    @pytest.mark.asyncio
    async def test_render_url_validates_input(self, pixelrag_service):
        """render_url debe validar URL antes de renderizar."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            await pixelrag_service.render_url("")

        with pytest.raises(ValueError, match="URL cannot be empty"):
            await pixelrag_service.render_url("   ")

        with pytest.raises(ValueError, match="Invalid URL format"):
            await pixelrag_service.render_url("invalid-url")

    @pytest.mark.asyncio
    async def test_render_url_lazy_inits(self, pixelrag_service):
        """render_url debe llamar a _lazy_init."""
        with patch.object(pixelrag_service, "_lazy_init", new_callable=AsyncMock) as mock_init:
            pixelrag_service._engine = None
            pixelrag_service._initialized = False

            try:
                await pixelrag_service.render_url("https://example.com")
            except RuntimeError:
                pass  # Esperado porque no hay engine real

            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_render_url_raises_when_no_engine(self, pixelrag_service):
        """render_url debe lanzar RuntimeError si no hay engine."""
        pixelrag_service._engine = None
        pixelrag_service._initialized = True

        with pytest.raises(RuntimeError, match="PixelRAG is not available"):
            await pixelrag_service.render_url("https://example.com")

    @pytest.mark.asyncio
    async def test_render_url_delegates_to_engine(self, pixelrag_service):
        """render_url debe delegar al engine pixelrag."""
        mock_engine = MagicMock()
        mock_engine.render_url = AsyncMock(return_value=b"fake_png")
        pixelrag_service._engine = mock_engine
        pixelrag_service._initialized = True

        result = await pixelrag_service.render_url("https://example.com")

        assert result == b"fake_png"
        mock_engine.render_url.assert_called_once_with("https://example.com")

    @pytest.mark.asyncio
    async def test_render_url_wraps_engine_errors(self, pixelrag_service):
        """render_url debe envolver errores del engine en RuntimeError."""
        mock_engine = MagicMock()
        mock_engine.render_url = AsyncMock(side_effect=Exception("Chromium crashed"))
        pixelrag_service._engine = mock_engine
        pixelrag_service._initialized = True

        with pytest.raises(RuntimeError, match="Render failed"):
            await pixelrag_service.render_url("https://example.com")


# Fixture para importar schemas
@pytest.fixture
def sample_screenshot_result():
    from app.schemas.analysis import ScreenshotResult
    from datetime import datetime

    return ScreenshotResult(
        image_bytes=b"fake_png",
        url="https://example.com",
        timestamp=datetime.now(),
        resolution=(1920, 1080),
    )