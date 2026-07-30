"""
Tests para el Scheduler — APScheduler y verificación comercial.

Verifica que el scheduler se inicia/detiene correctamente y
que la verificación comercial no lanza excepciones.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduler import start_scheduler, stop_scheduler, _run_commercial_check_sync


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

        # Verificar que tiene el job diario configurado
        jobs = scheduler.get_jobs()
        job_ids = [j.id for j in jobs]
        assert "commercial_check_daily" in job_ids

        stop_scheduler()

    def test_start_scheduler_idempotent(self):
        """Llamar start_scheduler dos veces no debe crear duplicados."""
        mock_factory = MagicMock()
        s1 = start_scheduler(mock_factory)
        s2 = start_scheduler(mock_factory)

        assert s1 is s2  # Misma instancia
        jobs = s1.get_jobs()
        assert len(jobs) == 1  # Solo un job

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

        mock_logger.info.assert_any_call("✅ APScheduler iniciado — barrido diario configurado")

        stop_scheduler()

    @patch("app.scheduler.logger")
    def test_scheduler_logs_warning_on_duplicate(self, mock_logger):
        """Debe loggear warning si se intenta iniciar dos veces."""
        mock_factory = MagicMock()
        s1 = start_scheduler(mock_factory)
        s2 = start_scheduler(mock_factory)

        mock_logger.warning.assert_called_once()

        stop_scheduler()
