"""
Gemini Vision Client — calls Gemini Vision API with retry/backoff
and parses structured JSON responses validated with Pydantic.

Uses google-generativeai library (legacy API compatible with tests).
"""

import asyncio
import io
import json
import logging
import os
from typing import Optional

from PIL import Image
from pydantic import ValidationError

from app.schemas.analysis import AnalysisProposal, ScreenshotResult

logger = logging.getLogger(__name__)

# Import google.generativeai at module level so tests can patch it
try:
    import google.generativeai as genai
except ImportError:
    genai = None


class GeminiClient:
    """
    Client for Google Gemini Vision API.

    Provides methods to analyze images and scraped content with
    retry logic, exponential backoff, and Pydantic validation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash-exp",
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_image_dimension: int = 1024,
        image_quality: int = 85,
    ):
        """
        Initialize the Gemini client.

        Args:
            api_key: Google AI API key (or uses GOOGLE_API_KEY env var)
            model: Model name to use
            max_retries: Maximum number of retry attempts
            base_delay: Base delay for exponential backoff (seconds)
            max_image_dimension: Maximum image dimension for optimization
            image_quality: JPEG quality for optimized images (1-100)
        """
        if genai is None:
            raise RuntimeError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai>=0.8.0"
            )

        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = model
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_image_dimension = max_image_dimension
        self.image_quality = image_quality

        if not self.api_key:
            raise ValueError(
                "Google API key not provided. "
                "Set GOOGLE_API_KEY env var or pass api_key parameter."
            )

        # Configure the API key
        genai.configure(api_key=self.api_key)

    def _optimize_image(self, image_bytes: bytes) -> bytes:
        """
        Optimize image for Gemini Vision API.

        Resizes if larger than max_image_dimension, converts to RGB,
        and saves as JPEG with configured quality.
        """
        img = Image.open(io.BytesIO(image_bytes))

        # Convert RGBA/P to RGB with white background
        if img.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode in ("RGBA", "LA"):
                background.paste(img, mask=img.split()[-1])
                img = background
            else:
                img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if needed
        max_dim = max(img.size)
        if max_dim > self.max_image_dimension:
            ratio = self.max_image_dimension / max_dim
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Save as optimized JPEG
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=self.image_quality, optimize=True)
        return output.getvalue()

    async def _call_with_retry(
        self,
        prompt: str,
        image_bytes: Optional[bytes] = None,
    ) -> str:
        """
        Call Gemini API with exponential backoff retry logic.

        Args:
            prompt: Text prompt for the model
            image_bytes: Optional image bytes to include

        Returns:
            Raw text response from Gemini

        Raises:
            Exception: After max retries exceeded
        """
        model = genai.GenerativeModel(self.model_name)
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if image_bytes:
                    response = await model.generate_content_async(
                        [prompt, {"mime_type": "image/jpeg", "data": image_bytes}]
                    )
                else:
                    response = await model.generate_content_async(prompt)
                return response.text
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        f"Gemini API call failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Gemini API call failed after {self.max_retries + 1} attempts: {e}")

        raise last_exception

    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        screenshot: Optional[ScreenshotResult] = None,
    ) -> AnalysisProposal:
        """
        Analyze an image using Gemini Vision API.

        Args:
            image_bytes: Raw image bytes
            prompt: Custom prompt (uses default if not provided)
            screenshot: Optional screenshot to also analyze

        Returns:
            Validated AnalysisProposal from Gemini response

        Raises:
            ValidationError: If Gemini response doesn't match expected schema
        """
        # Optimizar solo si hay bytes reales; con bytes vacíos se envía solo texto
        # (evita UnidentifiedImageError al intentar abrir un buffer vacío)
        optimized_bytes = self._optimize_image(image_bytes) if image_bytes else None

        # If screenshot provided, also optimize it
        screenshot_bytes = None
        if screenshot:
            screenshot_bytes = self._optimize_image(screenshot.image_bytes)

        default_prompt = (
            "Analyze this image and extract product information. "
            "Return a JSON object with exactly these fields: "
            "product_name (string), extracted_price (number), "
            "confidence_score (number between 0.0 and 1.0), "
            "raw_data (object with any additional details). "
            "Only return valid JSON, no additional text."
        )

        # Build content parts
        content_parts = [prompt or default_prompt]
        if image_bytes:
            content_parts.append({"mime_type": "image/jpeg", "data": optimized_bytes})
        if screenshot_bytes:
            content_parts.append({"mime_type": "image/jpeg", "data": screenshot_bytes})

        response_text = await self._call_with_retry(content_parts)

        return self._parse_and_validate(response_text)

    async def analyze_scraped_content(
        self,
        html_content: str,
        screenshot: ScreenshotResult,
        prompt: Optional[str] = None,
    ) -> AnalysisProposal:
        """
        Analyze scraped HTML content combined with screenshot.

        Args:
            html_content: Raw HTML from scraping
            screenshot: ScreenshotResult from PixelRAG
            prompt: Custom prompt (uses default if not provided)

        Returns:
            Validated AnalysisProposal from Gemini response
        """
        optimized_screenshot = self._optimize_image(screenshot.image_bytes)

        default_prompt = (
            "Analyze this web page content and screenshot to extract product information. "
            "The HTML content is provided below, along with a screenshot of the page. "
            "Return a JSON object with exactly these fields: "
            "product_name (string), extracted_price (number), "
            "confidence_score (number between 0.0 and 1.0), "
            "raw_data (object with any additional details). "
            "Only return valid JSON, no additional text.\n\n"
            f"HTML Content:\n{html_content[:5000]}"
        )

        content_parts = [prompt or default_prompt]
        content_parts.append({"mime_type": "image/jpeg", "data": optimized_screenshot})

        response_text = await self._call_with_retry(content_parts)

        return self._parse_and_validate(response_text)

    def _parse_and_validate(self, response_text: str) -> AnalysisProposal:
        """
        Parse Gemini response and validate with Pydantic.

        Args:
            response_text: Raw text response from Gemini

        Returns:
            Validated AnalysisProposal

        Raises:
            ValidationError: If response doesn't match schema
        """
        # Extract JSON from response (handle markdown code blocks)
        json_text = response_text.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        json_text = json_text.strip()

        # Parse JSON
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {response_text[:500]}")
            raise ValidationError.from_exception_data(
                "AnalysisProposal",
                [
                    {
                        "type": "json_invalid",
                        "loc": ("response",),
                        "msg": "Invalid JSON from Gemini",
                        "input": response_text[:500],
                        "ctx": {"error": "Invalid JSON from Gemini"},
                    }
                ],
            ) from e

        # Validate with Pydantic
        return AnalysisProposal(**data)