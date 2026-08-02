"""
Tests para Orchestrator — TDD RED → GREEN → REFACTOR
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.analysis.orchestrator import AnalysisOrchestrator
from app.services.analysis.scraper import ScrapedContent
from app.schemas.analysis import AnalysisProposal, ScreenshotResult


class TestAnalysisOrchestrator:
    """Tests del orquestador de análisis."""

    @pytest.fixture
    def mock_job_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_result_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_source_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_gemini(self):
        return AsyncMock()

    @pytest.fixture
    def mock_scraper(self):
        return AsyncMock()

    @pytest.fixture
    def mock_pixelrag(self):
        return AsyncMock()

    @pytest.fixture
    def mock_notifications(self):
        return AsyncMock()

    @pytest.fixture
    def orchestrator(
        self,
        mock_job_repo,
        mock_result_repo,
        mock_source_repo,
        mock_gemini,
        mock_scraper,
        mock_pixelrag,
        mock_notifications,
    ):
        return AnalysisOrchestrator(
            job_repo=mock_job_repo,
            result_repo=mock_result_repo,
            source_repo=mock_source_repo,
            gemini_client=mock_gemini,
            scraper=mock_scraper,
            pixelrag=mock_pixelrag,
            notification_service=mock_notifications,
        )

    @pytest.fixture
    def sample_job(self):
        from app.models.analysis import AnalysisJob, AnalysisStatus

        job = MagicMock(spec=AnalysisJob)
        job.id = uuid4()
        job.job_type = "url"
        job.input_data = {"url": "https://example.com/product"}
        job.status = AnalysisStatus.PENDING.value
        job.error_message = None
        job.started_at = None
        job.completed_at = None
        return job

    @pytest.fixture
    def sample_image_job(self):
        from app.models.analysis import AnalysisJob, AnalysisStatus

        job = MagicMock(spec=AnalysisJob)
        job.id = uuid4()
        job.job_type = "image"
        job.input_data = {"image_bytes": b"fake_image_bytes"}
        job.status = AnalysisStatus.PENDING.value
        job.error_message = None
        job.started_at = None
        job.completed_at = None
        return job

    @pytest.fixture
    def sample_proposal(self):
        return AnalysisProposal(
            product_name="Test Product",
            extracted_price=299.99,
            confidence_score=0.85,
            raw_data={"features": ["feature1", "feature2"]},
        )

    @pytest.fixture
    def sample_scraped(self):
        return ScrapedContent(
            url="https://example.com/product",
            title="Test Product",
            text="Product description with price $299.99",
            metadata={"og:price:amount": "299.99"},
            html_length=1000,
        )

    @pytest.fixture
    def sample_screenshot(self):
        return ScreenshotResult(
            image_bytes=b"fake_screenshot",
            url="https://example.com/product",
            timestamp=datetime.now(),
            resolution=(1920, 1080),
        )

    @pytest.mark.asyncio
    async def test_process_job_url_calls_scraper_and_gemini(
        self,
        orchestrator,
        mock_job_repo,
        mock_result_repo,
        mock_gemini,
        mock_scraper,
        mock_pixelrag,
        mock_notifications,
        sample_job,
        sample_proposal,
        sample_scraped,
        sample_screenshot,
    ):
        mock_job_repo.get_by_id.return_value = sample_job
        mock_scraper.scrape.return_value = sample_scraped
        mock_pixelrag.capture_for_analysis.return_value = sample_screenshot
        mock_gemini.analyze_scraped_content.return_value = sample_proposal

        # Mock result repo create
        from app.models.analysis import AnalysisResult
        mock_result = MagicMock(spec=AnalysisResult)
        mock_result.id = uuid4()
        mock_result_repo.create.return_value = mock_result

        result = await orchestrator.process_job(str(sample_job.id))

        assert result is not None
        mock_job_repo.get_by_id.assert_called_once()
        mock_scraper.scrape.assert_called_once_with(sample_job.input_data["url"])
        mock_pixelrag.capture_for_analysis.assert_called_once_with(sample_job.input_data["url"])
        # Con screenshot disponible, el orchestrator usa analyze_scraped_content (no analyze_image)
        mock_gemini.analyze_scraped_content.assert_called_once()
        mock_gemini.analyze_image.assert_not_called()
        mock_result_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_job_image_calls_gemini_directly(
        self,
        orchestrator,
        mock_job_repo,
        mock_result_repo,
        mock_gemini,
        mock_scraper,
        mock_pixelrag,
        mock_notifications,
        sample_image_job,
        sample_proposal,
    ):
        mock_job_repo.get_by_id.return_value = sample_image_job
        mock_gemini.analyze_image.return_value = sample_proposal

        from app.models.analysis import AnalysisResult
        mock_result = MagicMock(spec=AnalysisResult)
        mock_result.id = uuid4()
        mock_result_repo.create.return_value = mock_result

        result = await orchestrator.process_job(str(sample_image_job.id))

        assert result is not None
        mock_gemini.analyze_image.assert_called_once()
        mock_scraper.scrape.assert_not_called()
        mock_pixelrag.capture_for_analysis.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_job_not_found_returns_none(
        self,
        orchestrator,
        mock_job_repo,
    ):
        mock_job_repo.get_by_id.return_value = None

        result = await orchestrator.process_job(str(uuid4()))

        assert result is None

    @pytest.mark.asyncio
    async def test_process_job_marks_failed_on_error(
        self,
        orchestrator,
        mock_job_repo,
        mock_scraper,
        mock_pixelrag,
        mock_gemini,
        sample_job,
        sample_scraped,
    ):
        mock_job_repo.get_by_id.return_value = sample_job
        mock_scraper.scrape.return_value = sample_scraped
        mock_pixelrag.capture_for_analysis.side_effect = Exception("screenshot fail")
        mock_gemini.analyze_image.side_effect = Exception("Gemini API down")

        result = await orchestrator.process_job(str(sample_job.id))

        assert result is None
        # Job debe marcarse como failed (update recibe el dict como arg posicional)
        from unittest.mock import ANY

        mock_job_repo.update.assert_any_call(
            sample_job.id,
            {"status": "failed", "error_message": "Gemini API down", "completed_at": ANY},
        )

    @pytest.mark.asyncio
    async def test_approve_proposal_updates_status(
        self,
        orchestrator,
        mock_result_repo,
        mock_notifications,
    ):
        from app.models.analysis import AnalysisResult

        result_id = uuid4()
        mock_result = MagicMock(spec=AnalysisResult)
        mock_result.id = result_id
        mock_result.status = "proposal"
        mock_result.proposal_data = {
            "product_name": "Test Product",
            "extracted_price": 299.99,
            "confidence_score": 0.85,
            "raw_data": {},
        }
        # Valores reales para que los f-strings de notificación no exploten con MagicMock
        mock_result.product_name = "Test Product"
        mock_result.extracted_price = 299.99
        mock_result.currency = "USD"
        mock_result_repo.get_by_id.return_value = mock_result

        success = await orchestrator.approve_proposal(str(result_id))

        assert success is True
        mock_result_repo.update.assert_called()
        mock_notifications.create_notification.assert_called()

    @pytest.mark.asyncio
    async def test_approve_proposal_fails_if_not_proposal(
        self,
        orchestrator,
        mock_result_repo,
    ):
        from app.models.analysis import AnalysisResult

        result_id = uuid4()
        mock_result = MagicMock(spec=AnalysisResult)
        mock_result.id = result_id
        mock_result.status = "approved"  # Ya aprobado
        mock_result_repo.get_by_id.return_value = mock_result

        success = await orchestrator.approve_proposal(str(result_id))

        assert success is False

    @pytest.mark.asyncio
    async def test_reject_proposal_updates_status(
        self,
        orchestrator,
        mock_result_repo,
        mock_notifications,
    ):
        from app.models.analysis import AnalysisResult

        result_id = uuid4()
        mock_result = MagicMock(spec=AnalysisResult)
        mock_result.id = result_id
        mock_result.status = "proposal"
        mock_result_repo.get_by_id.return_value = mock_result

        success = await orchestrator.reject_proposal(str(result_id), "Low confidence")

        assert success is True
        mock_result_repo.update.assert_called()
        mock_notifications.create_notification.assert_called()

    @pytest.mark.asyncio
    async def test_process_job_marks_pipeline_success(
        self,
        orchestrator,
        mock_job_repo,
        mock_result_repo,
        mock_gemini,
        mock_scraper,
        mock_pixelrag,
        mock_notifications,
        sample_image_job,
        sample_proposal,
    ):
        """process_job DEBE registrar éxito en pipeline_state al completar (R-X03)."""
        import app.services.analysis.pipeline_state as ps_module
        ps_module.pipeline_state.active = False
        ps_module.pipeline_state.last_successful_run = None

        mock_job_repo.get_by_id.return_value = sample_image_job
        mock_gemini.analyze_image.return_value = sample_proposal

        from app.models.analysis import AnalysisResult
        mock_result = MagicMock(spec=AnalysisResult)
        mock_result.id = uuid4()
        mock_result_repo.create.return_value = mock_result

        result = await orchestrator.process_job(str(sample_image_job.id))

        assert result is not None
        assert ps_module.pipeline_state.last_successful_run is not None
        assert ps_module.pipeline_state.is_registered() is True

        # Limpiar estado del singleton para no contaminar otros tests
        ps_module.pipeline_state.active = False
        ps_module.pipeline_state.last_successful_run = None

    @pytest.mark.asyncio
    async def test_pixelrag_failure_falls_back_to_text_only(
        self,
        orchestrator,
        mock_job_repo,
        mock_result_repo,
        mock_pixelrag,
        mock_gemini,
        mock_scraper,
        sample_job,
        sample_proposal,
        sample_scraped,
    ):
        """Si el screenshot falla, el pipeline continúa con análisis solo texto."""
        mock_pixelrag.capture_for_analysis.side_effect = Exception("render failed")  # Falla

        mock_job_repo.get_by_id.return_value = sample_job
        mock_scraper.scrape.return_value = sample_scraped
        mock_gemini.analyze_image.return_value = sample_proposal

        from app.models.analysis import AnalysisResult
        mock_result = MagicMock(spec=AnalysisResult)
        mock_result.id = uuid4()
        mock_result_repo.create.return_value = mock_result

        result = await orchestrator.process_job(str(sample_job.id))

        # Debe continuar aunque screenshot falle
        assert result is not None
        mock_gemini.analyze_image.assert_called_once()