"""
Tests para el Scheduler — APScheduler y verificación comercial.

Verifica que el scheduler se inicia/detiene correctamente y
que la verificación comercial no lanza excepciones.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.scheduler import (
    start_scheduler,
    stop_scheduler,
    _run_commercial_check_sync,
    _run_analysis_monitor,
    _run_analysis_monitor_sync,
    ANALYSIS_MONITOR_INTERVAL_MINUTES,
)
from app.models.analysis import ScrapedSource, AnalysisJob


class TestScheduler:
    """Suite de tests para el scheduler."""

    def setup_method(self):
        """Limpia el estado global antes de cada test."""
        import app.scheduler as sched_mod
        sched_mod.scheduler = None
        sched_mod._executor = None

    def test_start_scheduler_creates_instance(self):
        """Debe crear un BackgroundScheduler al iniciar."""
        mock_factory = MagicMock()
        scheduler = start_scheduler(mock_factory)

        assert scheduler is not None
        assert scheduler.running is True

        # Verificar que tiene los dos jobs configurados
        jobs = scheduler.get_jobs()
        job_ids = [j.id for j in jobs]
        assert "commercial_check_daily" in job_ids
        assert "analysis_monitor" in job_ids

        stop_scheduler()

    def test_start_scheduler_idempotent(self):
        """Llamar start_scheduler dos veces no debe crear duplicados."""
        mock_factory = MagicMock()
        s1 = start_scheduler(mock_factory)
        s2 = start_scheduler(mock_factory)

        assert s1 is s2  # Misma instancia
        jobs = s1.get_jobs()
        assert len(jobs) == 2  # Dos jobs: commercial_check_daily y analysis_monitor

        stop_scheduler()

    def test_stop_scheduler_cleans_up(self):
        """Debe detener y limpiar el scheduler."""
        mock_factory = MagicMock()
        start_scheduler(mock_factory)

        stop_scheduler()

        import app.scheduler as sched_mod
        assert sched_mod.scheduler is None
        assert sched_mod._executor is None

    def test_stop_scheduler_idempotent(self):
        """Llamar stop_scheduler sin scheduler iniciado no debe fallar."""
        stop_scheduler()  # No debe lanzar excepción

    @pytest.mark.asyncio
    async def test_commercial_check_executes_without_error(self):
        """_run_commercial_check_sync debe ejecutarse sin error."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__.return_value = mock_session

        mock_factory = MagicMock()
        mock_factory.return_value = mock_session

        # No debe lanzar excepción
        _run_commercial_check_sync(mock_factory)

    def test_scheduler_job_interval(self):
        """El job diario debe tener trigger de 24 horas."""
        mock_factory = MagicMock()
        scheduler = start_scheduler(mock_factory)

        job = scheduler.get_job("commercial_check_daily")
        assert job is not None
        assert job.trigger.interval.total_seconds() == 86400  # 24h

        stop_scheduler()

    def test_scheduler_misfire_grace_time(self):
        """El job debe tener misfire_grace_time configurado."""
        mock_factory = MagicMock()
        scheduler = start_scheduler(mock_factory)

        job = scheduler.get_job("commercial_check_daily")
        assert job.misfire_grace_time == 3600

        stop_scheduler()

    @patch("app.scheduler.logger")
    def test_scheduler_logs_on_start(self, mock_logger):
        """Debe loggear cuando inicia correctamente."""
        mock_factory = MagicMock()
        scheduler = start_scheduler(mock_factory)

        mock_logger.info.assert_any_call("✅ APScheduler iniciado — barrido diario y monitor de análisis configurados")

        stop_scheduler()

    @patch("app.scheduler.logger")
    def test_scheduler_logs_warning_on_duplicate(self, mock_logger):
        """Debe loggear warning si se intenta iniciar dos veces."""
        mock_factory = MagicMock()
        s1 = start_scheduler(mock_factory)
        s2 = start_scheduler(mock_factory)

        mock_logger.warning.assert_called_once()

        stop_scheduler()


class TestAnalysisMonitor:
    """Tests para el job de monitoreo de análisis (analysis_monitor)."""

    def setup_method(self):
        """Limpia el estado global antes de cada test."""
        import app.scheduler as sched_mod
        sched_mod.scheduler = None
        sched_mod._executor = None

    @pytest.mark.asyncio
    async def test_sweep_validates_url_guard_private_ip(self):
        """Fuente con URL 127.0.0.1 → job failed sin fetch."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__.return_value = mock_session

        # Mock repo methods
        mock_source = MagicMock(spec=ScrapedSource)
        mock_source.id = uuid4()
        mock_source.url = "http://127.0.0.1/internal"
        mock_source.is_active = True
        mock_source.schedule_interval_minutes = 15
        mock_source.last_analyzed_at = None

        mock_factory = MagicMock()
        mock_factory.return_value = mock_session

        # Mock the repository get_all to return our source
        with patch("app.scheduler.ScrapedSourceRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = {"items": [mock_source], "total": 1, "page": 1, "per_page": 10}
            mock_repo_class.return_value = mock_repo

            # Mock AnalysisJobRepository.create to capture the call
            with patch("app.scheduler.AnalysisJobRepository") as mock_job_repo_class:
                mock_job_repo = AsyncMock()
                mock_job_repo_class.return_value = mock_job_repo

                # Act
                await _run_analysis_monitor(mock_factory)

                # Assert - job should be created with status=failed
                mock_job_repo.create.assert_called_once()
                call_args = mock_job_repo.create.call_args[0][0]
                assert call_args["job_type"] == "url"
                assert call_args["status"] == "failed"
                assert "SSRF guard" in call_args["error_message"]
                assert call_args["input_data"]["url"] == "http://127.0.0.1/internal"

    @pytest.mark.asyncio
    async def test_sweep_validates_url_guard_non_http(self):
        """ftp:// → job failed."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__.return_value = mock_session

        mock_source = MagicMock(spec=ScrapedSource)
        mock_source.id = uuid4()
        mock_source.url = "ftp://example.com/file"
        mock_source.is_active = True
        mock_source.schedule_interval_minutes = 15
        mock_source.last_analyzed_at = None

        mock_factory = MagicMock()
        mock_factory.return_value = mock_session

        with patch("app.scheduler.ScrapedSourceRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = {"items": [mock_source], "total": 1, "page": 1, "per_page": 10}
            mock_repo_class.return_value = mock_repo

            with patch("app.scheduler.AnalysisJobRepository") as mock_job_repo_class:
                mock_job_repo = AsyncMock()
                mock_job_repo_class.return_value = mock_job_repo

                await _run_analysis_monitor(mock_factory)

                mock_job_repo.create.assert_called_once()
                call_args = mock_job_repo.create.call_args[0][0]
                assert call_args["job_type"] == "url"
                assert call_args["status"] == "failed"
                assert "SSRF guard" in call_args["error_message"]
                assert call_args["input_data"]["url"] == "ftp://example.com/file"

    @pytest.mark.asyncio
    async def test_sweep_validates_url_guard_timeout(self):
        """Mock validate_external_url para timeout → job failed."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__.return_value = mock_session

        mock_source = MagicMock(spec=ScrapedSource)
        mock_source.id = uuid4()
        mock_source.url = "http://slow.example.com"
        mock_source.is_active = True
        mock_source.schedule_interval_minutes = 15
        mock_source.last_analyzed_at = None

        mock_factory = MagicMock()
        mock_factory.return_value = mock_session

        with patch("app.scheduler.ScrapedSourceRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = {"items": [mock_source], "total": 1, "page": 1, "per_page": 10}
            mock_repo_class.return_value = mock_repo

            with patch("app.scheduler.AnalysisJobRepository") as mock_job_repo_class:
                mock_job_repo = AsyncMock()
                mock_job_repo_class.return_value = mock_job_repo

                with patch("app.scheduler.validate_external_url") as mock_validate:
                    mock_validate.side_effect = ValueError("Timed out resolving host 'slow.example.com' after 5.0s")
                    await _run_analysis_monitor(mock_factory)

                    mock_job_repo.create.assert_called_once()
                    call_args = mock_job_repo.create.call_args[0][0]
                    assert call_args["job_type"] == "url"
                    assert call_args["status"] == "failed"
                    assert "SSRF guard" in call_args["error_message"]
                    assert "Timed out" in call_args["error_message"]

    @pytest.mark.asyncio
    async def test_sweep_public_url_creates_job(self):
        """URL pública → job creado 202."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__.return_value = mock_session

        mock_source = MagicMock(spec=ScrapedSource)
        mock_source.id = uuid4()
        mock_source.url = "https://example.com/product"
        mock_source.is_active = True
        mock_source.schedule_interval_minutes = 15
        mock_source.last_analyzed_at = None

        mock_factory = MagicMock()
        mock_factory.return_value = mock_session

        with patch("app.scheduler.ScrapedSourceRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = {"items": [mock_source], "total": 1, "page": 1, "per_page": 10}
            mock_repo_class.return_value = mock_repo

            with patch("app.scheduler.AnalysisJobRepository") as mock_job_repo_class:
                mock_job_repo = AsyncMock()
                mock_job_repo_class.return_value = mock_job_repo

                with patch("app.scheduler.validate_external_url") as mock_validate:
                    mock_validate.return_value = "https://example.com/product"
                    await _run_analysis_monitor(mock_factory)

                    mock_job_repo.create.assert_called_once()
                    call_args = mock_job_repo.create.call_args[0][0]
                    assert call_args["job_type"] == "url"
                    assert call_args["status"] == "pending"
                    assert call_args["input_data"]["url"] == "https://example.com/product"

    @pytest.mark.asyncio
    async def test_sweep_skips_inactive(self):
        """Fuente is_active=False → no crea job."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__.return_value = mock_session

        mock_factory = MagicMock()
        mock_factory.return_value = mock_session

        with patch("app.scheduler.ScrapedSourceRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = {"items": [], "total": 0, "page": 1, "per_page": 10}
            mock_repo_class.return_value = mock_repo

            with patch("app.scheduler.AnalysisJobRepository") as mock_job_repo_class:
                mock_job_repo = AsyncMock()
                mock_job_repo_class.return_value = mock_job_repo

                await _run_analysis_monitor(mock_factory)

                mock_job_repo.create.assert_not_called()
