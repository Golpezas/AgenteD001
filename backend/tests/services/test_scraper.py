"""
Tests para WebScraper — TDD RED → GREEN → REFACTOR
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.analysis.scraper import WebScraper, ScrapedContent, scrape_url


class TestWebScraper:
    """Tests del WebScraper."""

    @pytest.fixture
    def scraper(self):
        return WebScraper(timeout=5.0)

    @pytest.fixture
    def sample_html(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Product Page</title>
            <meta property="og:title" content="OG Product Title">
            <meta property="og:price:amount" content="299.99">
            <meta property="og:price:currency" content="USD">
            <meta name="description" content="Best product ever">
            <link rel="canonical" href="https://example.com/product">
            <script type="application/ld+json">
            {"@context": "https://schema.org", "@type": "Product", "name": "Test Product", "offers": {"price": "299.99"}}
            </script>
        </head>
        <body>
            <header><nav>Navigation</nav></header>
            <main>
                <h1>Test Product</h1>
                <p class="price">$299.99</p>
                <p>This is an amazing product with great features.</p>
            </main>
            <footer>Footer content</footer>
            <script>console.log('tracking');</script>
            <style>.hidden { display: none; }</style>
        </body>
        </html>
        """

    @pytest.mark.asyncio
    async def test_scrape_extracts_title_from_og(self, scraper, sample_html):
        with patch.object(scraper, "_get_client") as mock_client:
            mock_response = AsyncMock()
            mock_response.text = sample_html
            mock_response.url = "https://example.com/product"
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.get = AsyncMock(return_value=mock_response)

            result = await scraper.scrape("https://example.com/product")

            assert result.title == "OG Product Title"
            assert result.url == "https://example.com/product"

    @pytest.mark.asyncio
    async def test_scrape_extracts_main_text_excludes_nav_footer(self, scraper, sample_html):
        with patch.object(scraper, "_get_client") as mock_client:
            mock_response = AsyncMock()
            mock_response.text = sample_html
            mock_response.url = "https://example.com/product"
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.get = AsyncMock(return_value=mock_response)

            result = await scraper.scrape("https://example.com/product")

            assert "Test Product" in result.text
            assert "amazing product" in result.text
            assert "Navigation" not in result.text
            assert "Footer content" not in result.text
            assert "tracking" not in result.text

    @pytest.mark.asyncio
    async def test_scrape_extracts_metadata_og_and_json_ld(self, scraper, sample_html):
        with patch.object(scraper, "_get_client") as mock_client:
            mock_response = AsyncMock()
            mock_response.text = sample_html
            mock_response.url = "https://example.com/product"
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.get = AsyncMock(return_value=mock_response)

            result = await scraper.scrape("https://example.com/product")

            assert "og:title" in result.metadata
            assert result.metadata["og:title"] == "OG Product Title"
            assert "og:price:amount" in result.metadata
            assert "json_ld" in result.metadata
            assert len(result.metadata["json_ld"]) == 1

    @pytest.mark.asyncio
    async def test_scrape_handles_timeout(self, scraper):
        with patch.object(scraper, "_get_client") as mock_client:
            import httpx

            mock_client.return_value.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

            with pytest.raises(httpx.TimeoutException):
                await scraper.scrape("https://example.com/slow")

    @pytest.mark.asyncio
    async def test_scrape_handles_http_error(self, scraper):
        with patch.object(scraper, "_get_client") as mock_client:
            import httpx

            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.return_value.get = AsyncMock(
                side_effect=httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)
            )

            with pytest.raises(httpx.HTTPStatusError):
                await scraper.scrape("https://example.com/notfound")

    @pytest.mark.asyncio
    async def test_scrape_empty_url_raises(self, scraper):
        with pytest.raises(ValueError, match="URL cannot be empty"):
            await scraper.scrape("")

    @pytest.mark.asyncio
    async def test_scrape_whitespace_url_raises(self, scraper):
        with pytest.raises(ValueError, match="URL cannot be empty"):
            await scraper.scrape("   ")

    @pytest.mark.asyncio
    async def test_close_closes_client(self, scraper):
        mock_client = AsyncMock()
        mock_client.is_closed = False  # Important: is_closed check in close()
        scraper._client = mock_client

        await scraper.close()

        mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_url_helper_function(self, sample_html):
        with patch("app.services.analysis.scraper.WebScraper.scrape", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = ScrapedContent(
                url="https://example.com/product",
                title="Test Product",
                text="Product description",
                metadata={},
                html_length=100,
            )

            result = await scrape_url("https://example.com/product")

            assert isinstance(result, ScrapedContent)
            assert result.title == "Test Product"
            mock_scrape.assert_called_once_with("https://example.com/product")


class TestScrapedContent:
    """Tests del dataclass ScrapedContent."""

    def test_creation_with_all_fields(self):
        content = ScrapedContent(
            url="https://example.com",
            title="Test",
            text="Content",
            metadata={"key": "value"},
            html_length=1000,
            scraped_at="2024-01-01T00:00:00",
        )

        assert content.url == "https://example.com"
        assert content.title == "Test"
        assert content.text == "Content"
        assert content.metadata == {"key": "value"}
        assert content.html_length == 1000

    def test_creation_with_defaults(self):
        content = ScrapedContent(url="https://example.com")
        assert content.title is None
        assert content.text is None
        assert content.metadata == {}
        assert content.html_length == 0