"""
Tests para schemas Pydantic de Analysis — propuesta, job y result.

RED phase: estos tests referencian código que aún no existe,
por lo tanto fallarán con ModuleNotFoundError hasta que se
implementen los schemas (GREEN phase).
"""

import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.analysis import (
    AnalysisJobCreate,
    AnalysisJobResponse,
    AnalysisJobUpdate,
    AnalysisResultCreate,
    AnalysisResultResponse,
    AnalysisResultUpdate,
    AnalysisProposal,
    ScrapedSourceCreate,
    ScrapedSourceList,
    ScrapedSourceResponse,
    ScreenshotResult,
)


class TestAnalysisProposalSchema:
    """Suite de tests para AnalysisProposal."""

    def test_valid_proposal(self):
        """Debe validar una propuesta con todos los campos requeridos."""
        proposal = AnalysisProposal(
            product_name="Balcony Plan Premium",
            extracted_price=299.99,
            confidence_score=0.85,
            raw_data={"source": "gemini_vision", "fields": 5},
        )
        assert proposal.product_name == "Balcony Plan Premium"
        assert float(proposal.extracted_price) == 299.99
        assert proposal.confidence_score == 0.85
        assert proposal.raw_data == {"source": "gemini_vision", "fields": 5}

    def test_confidence_score_bounds(self):
        """confidence_score DEBE estar entre 0.0 y 1.0."""
        proposal = AnalysisProposal(
            product_name="Test",
            extracted_price=10.0,
            confidence_score=1.0,
            raw_data={},
        )
        assert proposal.confidence_score == 1.0

    def test_missing_product_name_raises(self):
        """Sin product_name debe lanzar ValidationError."""
        with pytest.raises(ValidationError) as exc:
            AnalysisProposal(
                extracted_price=10.0,
                confidence_score=0.5,
                raw_data={},
            )
        assert any("product_name" in str(e["loc"]) for e in exc.value.errors())

    def test_invalid_confidence_high(self):
        """confidence_score > 1.0 debe rechazar."""
        with pytest.raises(ValidationError) as exc:
            AnalysisProposal(
                product_name="Test",
                extracted_price=10.0,
                confidence_score=1.5,
                raw_data={},
            )
        assert any("confidence_score" in str(e["loc"]) for e in exc.value.errors())

    def test_invalid_confidence_negative(self):
        """confidence_score < 0.0 debe rechazar."""
        with pytest.raises(ValidationError) as exc:
            AnalysisProposal(
                product_name="Test",
                extracted_price=10.0,
                confidence_score=-0.1,
                raw_data={},
            )
        assert any("confidence_score" in str(e["loc"]) for e in exc.value.errors())


class TestScreenshotResultSchema:
    """Suite de tests para ScreenshotResult."""

    def test_valid_screenshot(self):
        """Debe validar un ScreenshotResult con todos los campos."""
        result = ScreenshotResult(
            url="https://example.com",
            timestamp=datetime(2026, 1, 15, 10, 30, 0),
            resolution=(1920, 1080),
        )
        assert result.url == "https://example.com"
        assert result.resolution == (1920, 1080)

    def test_image_bytes_default_empty(self):
        """image_bytes puede omitirse (por defecto vacío)."""
        result = ScreenshotResult(
            url="https://example.com",
            timestamp=datetime(2026, 1, 15, 10, 30, 0),
            resolution=(1920, 1080),
        )
        assert result.image_bytes == b""

    def test_screenshot_with_image_bytes(self):
        """image_bytes puede establecerse explícitamente."""
        png_data = b"\x89PNG\r\n\x1a\nfake_png_content"
        result = ScreenshotResult(
            url="https://example.com",
            timestamp=datetime(2026, 1, 15, 10, 30, 0),
            resolution=(1920, 1080),
            image_bytes=png_data,
        )
        assert result.image_bytes == png_data


class TestAnalysisJobSchema:
    """Suite de tests para esquemas de AnalysisJob."""

    def test_job_create_minimum(self):
        """AnalysisJobCreate requiere únicamente job_type e input_data."""
        create = AnalysisJobCreate(
            job_type="image",
            input_data={"image_url": "https://example.com/photo.jpg"},
        )
        assert create.job_type == "image"
        assert create.input_data == {"image_url": "https://example.com/photo.jpg"}

    def test_job_create_with_error_message(self):
        """AnalysisJobCreate puede incluir error_message."""
        create = AnalysisJobCreate(
            job_type="url",
            input_data={"url": "https://example.com"},
            error_message="Timeout",
        )
        assert create.error_message == "Timeout"

    def test_job_update_all_optional(self):
        """AnalysisJobUpdate todos los campos son opcionales."""
        update = AnalysisJobUpdate()
        assert update.job_type is None
        assert update.input_data is None

    def test_job_update_partial(self):
        """AnalysisJobUpdate permite actualizar solo algunos campos."""
        update = AnalysisJobUpdate(status="processing")
        assert update.status == "processing"
        assert update.job_type is None

    def test_job_response_includes_metadata(self):
        """AnalysisJobResponse debe incluir id y timestamps."""
        response = AnalysisJobResponse(
            id=uuid.uuid4(),
            job_type="url",
            input_data={"url": "https://example.com"},
            status="pending",
            result_id=None,
            error_message=None,
            is_active=True,
            created_at=datetime(2026, 1, 15, 10, 0, 0),
            updated_at=datetime(2026, 1, 15, 10, 0, 0),
        )
        assert response.id is not None
        assert response.created_at is not None


class TestAnalysisResultSchema:
    """Suite de tests para esquemas de AnalysisResult."""

    def test_result_create_minimum(self):
        """AnalysisResultCreate requiere job_id."""
        create = AnalysisResultCreate(
            job_id=uuid.uuid4(),
        )
        assert create.job_id is not None
        assert create.status == "proposal"

    def test_result_create_full(self):
        """AnalysisResultCreate acepta todos los campos."""
        create = AnalysisResultCreate(
            job_id=uuid.uuid4(),
            status="proposal",
            product_name="Test Product",
            extracted_price=99.99,
            currency="ARS",
            confidence_score=0.92,
            proposal_data={"source": "gemini"},
        )
        assert create.product_name == "Test Product"
        assert float(create.extracted_price) == 99.99
        assert create.currency == "ARS"

    def test_result_response_includes_metadata(self):
        """AnalysisResultResponse debe incluir id y timestamps."""
        response = AnalysisResultResponse(
            id=uuid.uuid4(),
            job_id=uuid.uuid4(),
            status="proposal",
            product_name="Test",
            extracted_price=50.0,
            currency="ARS",
            confidence_score=0.8,
            raw_data=None,
            proposal_data=None,
            is_active=True,
            created_at=datetime(2026, 1, 15, 10, 0, 0),
            updated_at=datetime(2026, 1, 15, 10, 0, 0),
        )
        assert response.id is not None
        assert response.created_at is not None

    def test_result_response_with_accepted_status(self):
        """AnalysisResultResponse acepta status=accepted."""
        response = AnalysisResultResponse(
            id=uuid.uuid4(),
            job_id=uuid.uuid4(),
            status="accepted",
            product_name="Accepted Product",
            extracted_price=100.0,
            is_active=True,
            created_at=datetime(2026, 1, 15, 10, 0, 0),
            updated_at=datetime(2026, 1, 15, 10, 0, 0),
        )
        assert response.status == "accepted"


class TestScrapedSourceSchema:
    """Schemas de ScrapedSource: url str 1..2048 (no HttpUrl, sin normalización)."""

    def test_create_valid_full(self):
        create = ScrapedSourceCreate(
            url="https://competidor.com/products",
            name="Competidor Principal",
            schedule_interval_minutes=60,
        )
        assert create.url == "https://competidor.com/products"
        assert create.name == "Competidor Principal"
        assert create.schedule_interval_minutes == 60

    def test_create_valid_optional_fields_none(self):
        create = ScrapedSourceCreate(url="https://example.com")
        assert create.url == "https://example.com"
        assert create.name is None
        assert create.schedule_interval_minutes is None

    def test_create_url_empty_rejected(self):
        with pytest.raises(ValidationError):
            ScrapedSourceCreate(url="")

    def test_create_url_exceeds_max_length_rejected(self):
        with pytest.raises(ValidationError):
            ScrapedSourceCreate(url="x" * 2049)

    def test_create_url_keeps_exact_value_no_normalization(self):
        """url es str validado por rango, NO HttpUrl: no se normaliza ni se punycodea."""
        create = ScrapedSourceCreate(url="HTTPS://Ejemplo.Com/")
        assert create.url == "HTTPS://Ejemplo.Com/"

    def test_response_includes_metadata(self):
        response = ScrapedSourceResponse(
            id=uuid.uuid4(),
            url="https://example.com",
            name="Example",
            schedule_interval_minutes=30,
            last_analyzed_at=None,
            is_active=True,
            created_at=datetime(2026, 1, 15, 10, 0, 0),
            updated_at=datetime(2026, 1, 15, 10, 0, 0),
        )
        assert response.id is not None
        assert response.url == "https://example.com"
        assert response.is_active is True
        assert response.last_analyzed_at is None

    def test_list_shape(self):
        item = ScrapedSourceResponse(
            id=uuid.uuid4(),
            url="https://example.com",
            name=None,
            schedule_interval_minutes=None,
            last_analyzed_at=None,
            is_active=True,
            created_at=datetime(2026, 1, 15, 10, 0, 0),
            updated_at=datetime(2026, 1, 15, 10, 0, 0),
        )
        listing = ScrapedSourceList(items=[item], total=1, page=1, per_page=10)
        assert listing.total == 1
        assert listing.page == 1
        assert listing.per_page == 10
        assert listing.items[0].url == "https://example.com"
