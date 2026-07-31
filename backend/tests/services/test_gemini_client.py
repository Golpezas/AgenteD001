"""
Tests for GeminiClient — Gemini Vision API client with retry/backoff.

RED phase: these tests reference code that doesn't exist yet.
They will fail until the implementation is complete (GREEN phase).
"""

import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError
from PIL import Image

from app.schemas.analysis import AnalysisProposal, ScreenshotResult


def _make_test_image_bytes(size=(100, 100), color="red", format="PNG"):
    """Create valid test image bytes."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


class TestGeminiClient:
    """Suite of tests for GeminiClient."""

    @pytest.mark.asyncio
    async def test_client_can_be_imported(self):
        """Should be able to import the client."""
        from app.services.analysis.gemini_client import GeminiClient  # noqa: F401
        assert True

    @pytest.mark.asyncio
    async def test_analyze_image_returns_proposal(self):
        """Should return AnalysisProposal for valid image analysis."""
        from app.services.analysis.gemini_client import GeminiClient

        # Mock the Gemini API response
        mock_response = {
            "product_name": "Test Product",
            "extracted_price": 99.99,
            "confidence_score": 0.92,
            "raw_data": {"source": "gemini_vision", "fields": 4},
        }

        with patch("app.services.analysis.gemini_client.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(
                return_value=MagicMock(text='{"product_name": "Test Product", "extracted_price": 99.99, "confidence_score": 0.92, "raw_data": {"source": "gemini_vision", "fields": 4}}')
            )
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()

            client = GeminiClient(api_key="test-key")
            result = await client.analyze_image(_make_test_image_bytes())

            assert isinstance(result, AnalysisProposal)
            assert result.product_name == "Test Product"
            assert float(result.extracted_price) == 99.99
            assert result.confidence_score == 0.92

    @pytest.mark.asyncio
    async def test_analyze_image_with_screenshot_returns_proposal(self):
        """Should return AnalysisProposal when analyzing image + screenshot."""
        from app.services.analysis.gemini_client import GeminiClient

        with patch("app.services.analysis.gemini_client.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(
                return_value=MagicMock(text='{"product_name": "Combined Product", "extracted_price": 149.99, "confidence_score": 0.88, "raw_data": {"source": "gemini_vision", "fields": 5}}')
            )
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()

            client = GeminiClient(api_key="test-key")
            screenshot = ScreenshotResult(
                image_bytes=_make_test_image_bytes(),
                url="https://example.com",
                timestamp="2026-01-15T10:30:00",
                resolution=(1920, 1080),
            )
            result = await client.analyze_image(_make_test_image_bytes(), screenshot=screenshot)

            assert isinstance(result, AnalysisProposal)
            assert result.product_name == "Combined Product"
            assert float(result.extracted_price) == 149.99

    @pytest.mark.asyncio
    async def test_analyze_image_invalid_json_raises(self):
        """Should raise ValidationError when Gemini returns invalid JSON."""
        from app.services.analysis.gemini_client import GeminiClient

        with patch("app.services.analysis.gemini_client.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(
                return_value=MagicMock(text="not valid json")
            )
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()

            client = GeminiClient(api_key="test-key")
            with pytest.raises(ValidationError):
                await client.analyze_image(_make_test_image_bytes())

    @pytest.mark.asyncio
    async def test_analyze_image_empty_bytes_text_only(self):
        """Should skip _optimize_image and analyze text-only when image_bytes is empty."""
        from app.services.analysis.gemini_client import GeminiClient

        with patch("app.services.analysis.gemini_client.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(
                return_value=MagicMock(text='{"product_name": "Text Product", "extracted_price": 10.0, "confidence_score": 0.9, "raw_data": {}}')
            )
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()

            client = GeminiClient(api_key="test-key")
            with patch.object(client, "_optimize_image", wraps=client._optimize_image) as mock_optimize:
                result = await client.analyze_image(
                    image_bytes=b"",
                    prompt="Analyze this text",
                )

            # No debe intentar optimizar bytes vacíos (falla con UnidentifiedImageError)
            mock_optimize.assert_not_called()
            assert isinstance(result, AnalysisProposal)
            assert result.product_name == "Text Product"
            assert float(result.extracted_price) == 10.0

    @pytest.mark.asyncio
    async def test_analyze_image_missing_fields_raises(self):
        """Should raise ValidationError when Gemini returns JSON missing required fields."""
        from app.services.analysis.gemini_client import GeminiClient

        with patch("app.services.analysis.gemini_client.genai") as mock_genai:
            mock_model = MagicMock()
            # Missing product_name
            mock_model.generate_content_async = AsyncMock(
                return_value=MagicMock(text='{"extracted_price": 99.99, "confidence_score": 0.9, "raw_data": {}}')
            )
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()

            client = GeminiClient(api_key="test-key")
            with pytest.raises(ValidationError) as exc:
                await client.analyze_image(_make_test_image_bytes())
            assert any("product_name" in str(e["loc"]) for e in exc.value.errors())

    @pytest.mark.asyncio
    async def test_analyze_image_confidence_out_of_bounds_raises(self):
        """Should raise ValidationError when confidence_score is out of bounds."""
        from app.services.analysis.gemini_client import GeminiClient

        with patch("app.services.analysis.gemini_client.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(
                return_value=MagicMock(text='{"product_name": "Test", "extracted_price": 99.99, "confidence_score": 1.5, "raw_data": {}}')
            )
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()

            client = GeminiClient(api_key="test-key")
            with pytest.raises(ValidationError) as exc:
                await client.analyze_image(_make_test_image_bytes())
            assert any("confidence_score" in str(e["loc"]) for e in exc.value.errors())

    @pytest.mark.asyncio
    async def test_analyze_image_retry_on_transient_error(self):
        """Should retry on transient API errors (exponential backoff)."""
        from app.services.analysis.gemini_client import GeminiClient

        with patch("app.services.analysis.gemini_client.genai") as mock_genai:
            mock_model = MagicMock()
            # First two calls fail, third succeeds
            mock_model.generate_content_async = AsyncMock(
                side_effect=[
                    Exception("Rate limit"),
                    Exception("Timeout"),
                    MagicMock(text='{"product_name": "Retry Product", "extracted_price": 50.0, "confidence_score": 0.75, "raw_data": {}}'),
                ]
            )
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()

            client = GeminiClient(api_key="test-key", max_retries=3)
            result = await client.analyze_image(_make_test_image_bytes())

            assert isinstance(result, AnalysisProposal)
            assert result.product_name == "Retry Product"
            assert mock_model.generate_content_async.call_count == 3

    @pytest.mark.asyncio
    async def test_analyze_image_max_retries_exceeded_raises(self):
        """Should raise after max retries exceeded."""
        from app.services.analysis.gemini_client import GeminiClient

        with patch("app.services.analysis.gemini_client.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(
                side_effect=Exception("Persistent error")
            )
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()

            client = GeminiClient(api_key="test-key", max_retries=2)
            with pytest.raises(Exception, match="Persistent error"):
                await client.analyze_image(_make_test_image_bytes())

            assert mock_model.generate_content_async.call_count == 3  # initial + 2 retries

    @pytest.mark.asyncio
    async def test_optimize_image_resizes_large_image(self):
        """Should resize images larger than max dimension."""
        from app.services.analysis.gemini_client import GeminiClient
        from PIL import Image
        import io

        # Create a large test image (3000x2000)
        large_img = Image.new("RGB", (3000, 2000), color="red")
        img_bytes = io.BytesIO()
        large_img.save(img_bytes, format="PNG")
        img_bytes = img_bytes.getvalue()

        client = GeminiClient(api_key="test-key", max_image_dimension=1024)
        optimized = client._optimize_image(img_bytes)

        # Verify it was resized
        optimized_img = Image.open(io.BytesIO(optimized))
        assert max(optimized_img.size) <= 1024

    @pytest.mark.asyncio
    async def test_optimize_image_preserves_small_image(self):
        """Should not resize images already within limits."""
        from app.services.analysis.gemini_client import GeminiClient
        from PIL import Image
        import io

        # Create a small test image (500x500)
        small_img = Image.new("RGB", (500, 500), color="blue")
        img_bytes = io.BytesIO()
        small_img.save(img_bytes, format="PNG")
        img_bytes = img_bytes.getvalue()

        client = GeminiClient(api_key="test-key", max_image_dimension=1024)
        optimized = client._optimize_image(img_bytes)

        # Verify it was not resized
        optimized_img = Image.open(io.BytesIO(optimized))
        assert optimized_img.size == (500, 500)

    @pytest.mark.asyncio
    async def test_optimize_image_converts_to_rgb(self):
        """Should convert RGBA images to RGB."""
        from app.services.analysis.gemini_client import GeminiClient
        from PIL import Image
        import io

        # Create an RGBA image
        rgba_img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        img_bytes = io.BytesIO()
        rgba_img.save(img_bytes, format="PNG")
        img_bytes = img_bytes.getvalue()

        client = GeminiClient(api_key="test-key")
        optimized = client._optimize_image(img_bytes)

        optimized_img = Image.open(io.BytesIO(optimized))
        assert optimized_img.mode == "RGB"

    @pytest.mark.asyncio
    async def test_analyze_scraped_content_returns_proposal(self):
        """Should analyze scraped HTML content + screenshot."""
        from app.services.analysis.gemini_client import GeminiClient

        with patch("app.services.analysis.gemini_client.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(
                return_value=MagicMock(text='{"product_name": "Scraped Product", "extracted_price": 75.50, "confidence_score": 0.82, "raw_data": {"source": "gemini_vision", "fields": 3}}')
            )
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()

            client = GeminiClient(api_key="test-key")
            result = await client.analyze_scraped_content(
                html_content="<html><body>Product page</body></html>",
                screenshot=ScreenshotResult(
                    image_bytes=_make_test_image_bytes(),
                    url="https://example.com",
                    timestamp="2026-01-15T10:30:00",
                    resolution=(1920, 1080),
                ),
            )

            assert isinstance(result, AnalysisProposal)
            assert result.product_name == "Scraped Product"
            assert float(result.extracted_price) == 75.50