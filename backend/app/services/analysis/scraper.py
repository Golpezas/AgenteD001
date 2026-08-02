"""
Web Scraper — extrae contenido HTML, metadata y texto principal
de páginas web para análisis con Gemini Vision.

Usa httpx para HTTP async + BeautifulSoup para parsing.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ScrapedContent:
    """Contenido extraído de una página web."""

    url: str
    title: Optional[str] = None
    text: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    html_length: int = 0
    scraped_at: Optional[str] = None


class WebScraper:
    """
    Scraper asíncrono para extraer contenido de páginas web.

    Características:
    - Timeout configurable
    - User-Agent realista
    - Extrae título, texto principal, metadata Open Graph
    - Manejo de errores y rate limiting básico
    """

    def __init__(
        self,
        timeout: float = 15.0,
        user_agent: str = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        max_redirects: int = 5,
    ):
        self.timeout = timeout
        self.user_agent = user_agent
        self.max_redirects = max_redirects
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
                max_redirects=self.max_redirects,
            )
        return self._client

    async def close(self) -> None:
        """Cierra el cliente HTTP."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def scrape(self, url: str) -> ScrapedContent:
        """
        Extrae contenido de una URL.

        Args:
            url: URL a scrapear

        Returns:
            ScrapedContent con título, texto, metadata

        Raises:
            httpx.HTTPError: Si falla la request
            ValueError: Si la URL es inválida
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")

        client = await self._get_client()

        try:
            logger.debug(f"Scraping {url}")
            response = await client.get(url)
            response.raise_for_status()

            html = response.text
            soup = BeautifulSoup(html, "lxml")

            # Extraer título
            title = self._extract_title(soup)

            # Extraer texto principal (limpiando scripts, styles, nav, etc.)
            text = self._extract_main_text(soup)

            # Extraer metadata (Open Graph, meta tags, JSON-LD)
            metadata = self._extract_metadata(soup, response.url)

            from datetime import datetime

            return ScrapedContent(
                url=str(response.url),
                title=title,
                text=text,
                metadata=metadata,
                html_length=len(html),
                scraped_at=datetime.utcnow().isoformat(),
            )

        except httpx.TimeoutException as e:
            logger.error(f"Timeout scraping {url}: {e}")
            raise httpx.TimeoutException(f"Timeout after {self.timeout}s") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error scraping {url}: {e.response.status_code}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error scraping {url}: {e}")
            raise

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrae el título de la página."""
        # Open Graph title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # Meta title
        meta_title = soup.find("meta", attrs={"name": "title"})
        if meta_title and meta_title.get("content"):
            return meta_title["content"].strip()

        # HTML title tag
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        # h1 como fallback
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        return None

    def _extract_main_text(self, soup: BeautifulSoup) -> str:
        """
        Extrae el texto principal limpiando elementos no deseados.

        Remueve: script, style, nav, header, footer, aside, noscript,
        iframe, form, button, elementos con class/id que sugieren
        navegación, publicidad, sidebar, etc.
        """
        # Clonar para no modificar el original si se reutiliza
        soup = BeautifulSoup(str(soup), "lxml")

        # Elementos a remover completamente
        for tag in soup.find_all(
            [
                "script",
                "style",
                "nav",
                "header",
                "footer",
                "aside",
                "noscript",
                "iframe",
                "form",
                "button",
                "input",
                "select",
                "textarea",
            ]
        ):
            tag.decompose()

        # Clases/IDs comunes de elementos no contenido
        noise_selectors = [
            "[class*='nav']",
            "[class*='menu']",
            "[class*='sidebar']",
            "[class*='footer']",
            "[class*='header']",
            "[class*='ad']",
            "[class*='banner']",
            "[class*='cookie']",
            "[class*='popup']",
            "[class*='modal']",
            "[class*='newsletter']",
            "[id*='nav']",
            "[id*='menu']",
            "[id*='sidebar']",
            "[id*='footer']",
            "[id*='header']",
        ]

        for selector in noise_selectors:
            for tag in soup.select(selector):
                tag.decompose()

        # Obtener texto de los elementos restantes
        # Priorizar main, article, section, div con contenido
        main_content = soup.find("main") or soup.find("article") or soup.find("section") or soup.body

        if main_content:
            text = main_content.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)

        # Limpiar whitespace excesivo
        import re

        text = re.sub(r"\s+", " ", text).strip()

        return text[:50000]  # Limitar a 50k chars

    def _extract_metadata(
        self, soup: BeautifulSoup, response_url: httpx.URL
    ) -> dict:
        """Extrae metadata estructurada: Open Graph, Twitter Cards, JSON-LD, meta tags."""
        metadata = {}

        # Open Graph
        for meta in soup.find_all("meta", property=lambda x: x and x.startswith("og:")):
            key = meta.get("property", "").replace("og:", "")
            if key and meta.get("content"):
                metadata[f"og:{key}"] = meta["content"]

        # Twitter Cards
        for meta in soup.find_all("meta", attrs={"name": lambda x: x and x.startswith("twitter:")}):
            key = meta.get("name", "").replace("twitter:", "")
            if key and meta.get("content"):
                metadata[f"twitter:{key}"] = meta["content"]

        # Meta tags estándar
        for meta in soup.find_all("meta", attrs={"name": True}):
            name = meta.get("name")
            content = meta.get("content")
            if name and content and not name.startswith("twitter:"):
                metadata[name] = content

        # JSON-LD structured data
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json

                data = json.loads(script.string)
                if isinstance(data, dict):
                    metadata.setdefault("json_ld", []).append(data)
                elif isinstance(data, list):
                    metadata.setdefault("json_ld", []).extend(data)
            except (json.JSONDecodeError, TypeError):
                pass

        # Canonical URL
        canonical = soup.find("link", rel="canonical")
        if canonical and canonical.get("href"):
            metadata["canonical"] = canonical["href"]

        # Favicon
        favicon = soup.find("link", rel=lambda x: x and "icon" in x.lower())
        if favicon and favicon.get("href"):
            metadata["favicon"] = favicon["href"]

        return metadata


async def scrape_url(url: str, timeout: float = 15.0) -> ScrapedContent:
    """
    Función helper para scrapear una URL simple.

    Args:
        url: URL a scrapear
        timeout: Timeout en segundos

    Returns:
        ScrapedContent
    """
    scraper = WebScraper(timeout=timeout)
    try:
        return await scraper.scrape(url)
    finally:
        await scraper.close()