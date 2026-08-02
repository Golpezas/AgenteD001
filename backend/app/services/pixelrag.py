"""
Servicio PixelRAG — wrapper lazy para renderizado con pixelshot.

La inicialización es lazy: no se importa pixelrag hasta
el primer uso, permitiendo que la app arranque sin
dependencias de Chromium.
"""

import importlib
import io
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from PIL import Image

from app.schemas.analysis import ScreenshotResult


class PixelRAGService:
    """Wrapper service para PixelRAG (pixelshot)."""

    def __init__(self):
        self._engine: Optional[object] = None
        self._initialized: bool = False

    async def _lazy_init(self) -> None:
        """
        Inicializa el engine de PixelRAG de forma lazy.

        Solo se llama en el primer uso real de renderizado.
        """
        if self._initialized:
            return

        try:
            pixelrag = importlib.import_module("pixelrag")
            self._engine = pixelrag
            self._initialized = True
        except ImportError:
            self._engine = None
            self._initialized = True

    def _validate_url(self, url: str) -> None:
        """Valida que la URL sea válida."""
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")

    async def render_url(self, url: str) -> bytes:
        """
        Renderiza una URL y retorna los bytes de la imagen.

        Args:
            url: URL a renderizar.

        Returns:
            bytes: Imagen PNG del renderizado.

        Raises:
            ValueError: Si la URL es inválida o vacía.
            RuntimeError: Si PixelRAG no está disponible.
        """
        self._validate_url(url)
        await self._lazy_init()

        if self._engine is None:
            raise RuntimeError("PixelRAG is not available")

        # Delegar a pixelrag.render_url
        try:
            result = await self._engine.render_url(url)
            return result
        except Exception as e:
            raise RuntimeError(f"Render failed: {e}") from e

    async def capture_for_analysis(self, url: str) -> ScreenshotResult:
        """
        Captura un screenshot de la URL para el pipeline de análisis.

        Reutiliza la misma instancia de pixelshot que render_url.

        Args:
            url: URL a capturar.

        Returns:
            ScreenshotResult con los bytes PNG del renderizado, la URL,
            el timestamp de captura y la resolución de la imagen.

        Raises:
            ValueError: Si la URL es inválida o vacía.
            RuntimeError: Si PixelRAG no está disponible o el render falla.
        """
        self._validate_url(url)
        await self._lazy_init()

        if self._engine is None:
            raise RuntimeError("PixelRAG is not available")

        # Los errores del engine se propagan envueltos en RuntimeError (igual que render_url)
        try:
            png_bytes = await self._engine.render_url(url)
        except Exception as e:
            raise RuntimeError(f"Render failed: {e}") from e

        # Derivar resolución abriendo la imagen PNG con PIL
        img = Image.open(io.BytesIO(png_bytes))

        return ScreenshotResult(
            image_bytes=png_bytes,
            url=url,
            timestamp=datetime.now(),
            resolution=img.size,
        )

    async def health(self) -> dict:
        """Retorna el estado del servicio."""
        await self._lazy_init()
        return {
            "status": "available" if self._engine is not None else "unavailable",
        }
