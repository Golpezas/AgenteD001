"""
Planificador de tareas periódicas — APScheduler BackgroundScheduler.

Ejecuta un barrido diario de reglas de negocio que genera
notificaciones de tipo business y un monitoreo periódico de
fuentes de análisis (ScrapedSource). Corre en un ThreadPoolExecutor
separado para no bloquear el event loop de FastAPI.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.analysis import AnalysisJob, ScrapedSource
from app.repositories.analysis import AnalysisJobRepository, ScrapedSourceRepository
from app.services.analysis.pipeline_state import pipeline_state
from app.services.analysis.url_guard import validate_external_url
from app.services.notification import NotificationService

logger = logging.getLogger("uvicorn")

# Instancia global del scheduler
scheduler: BackgroundScheduler | None = None
_executor: ThreadPoolExecutor | None = None

# Intervalo del monitor de análisis en minutos
ANALYSIS_MONITOR_INTERVAL_MINUTES = 15


def _run_commercial_check_sync(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """
    Ejecuta la verificación comercial (síncrono, corre en thread separado).

    Crea su propio event loop y sesión para operar fuera del loop principal.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _check():
            async with session_factory() as session:
                service = NotificationService(session)
                await service.force_commercial_check()

        loop.run_until_complete(_check())
        loop.close()
    except Exception as e:
        logger.error(f"Error en verificación comercial programada: {e}")


async def _run_analysis_monitor(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """
    Ejecuta el monitoreo periódico de fuentes de análisis (async).

    Para cada fuente activa, valida la URL con el SSRF guard antes de crear el job.
    Si la validación falla, crea un job con status="failed" y error_message.
    """
    async with session_factory() as session:
        source_repo = ScrapedSourceRepository(session)
        job_repo = AnalysisJobRepository(session)

        # Obtener todas las fuentes activas
        result = await source_repo.get_all(filters={"is_active": True})
        sources = result.get("items", [])

        for source in sources:
            # Respetar schedule_interval_minutes: saltar si last_analyzed_at es reciente
            if source.last_analyzed_at:
                interval = source.schedule_interval_minutes or ANALYSIS_MONITOR_INTERVAL_MINUTES
                next_run = source.last_analyzed_at + timedelta(minutes=interval)
                now = datetime.now(source.last_analyzed_at.tzinfo) if source.last_analyzed_at.tzinfo else datetime.utcnow()
                if now < next_run:
                    continue

            # Validar URL con SSRF guard ANTES de crear el job
            try:
                validated_url = await validate_external_url(source.url)
            except ValueError as e:
                # Log y crear job con status=failed
                logger.warning(f"SSRF guard rejected URL for source {source.id}: {e}")
                await job_repo.create(
                    {
                        "id": uuid4(),
                        "job_type": "url",
                        "input_data": {"url": source.url},
                        "status": "failed",
                        "error_message": f"SSRF guard: {e}",
                        "is_active": True,
                    }
                )
                # Actualizar last_analyzed_at incluso en fallo para evitar retry-storm
                await source_repo.update(source.id, {"last_analyzed_at": datetime.utcnow()})
                continue

            # Crear job con la URL validada
            await job_repo.create(
                {
                    "id": uuid4(),
                    "job_type": "url",
                    "input_data": {"url": validated_url},
                    "status": "pending",
                    "is_active": True,
                }
            )

            # Actualizar last_analyzed_at
            await source_repo.update(source.id, {"last_analyzed_at": datetime.utcnow()})


def _run_analysis_monitor_sync(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """
    Wrapper síncrono para el scheduler (corre en thread separado).

    Crea su propio event loop y ejecuta la lógica async.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_run_analysis_monitor(session_factory))
        loop.close()
    except Exception as e:
        logger.error(f"Error en monitoreo de análisis programado: {e}")


def start_scheduler(
    session_factory: async_sessionmaker[AsyncSession],
) -> BackgroundScheduler:
    """
    Inicia el APScheduler BackgroundScheduler con el barrido diario y el monitor de análisis.

    El scheduler ejecuta:
    - _run_commercial_check_sync cada 24 horas
    - _run_analysis_monitor_sync cada 15 minutos (ANALYSIS_MONITOR_INTERVAL_MINUTES)
    Se ejecuta en un ThreadPoolExecutor separado para no bloquear
    el event loop de la aplicación.
    """
    global scheduler, _executor

    if scheduler is not None:
        logger.warning("Scheduler ya está en ejecución — ignorando start_scheduler()")
        return scheduler

    _executor = ThreadPoolExecutor(max_workers=1)
    scheduler = BackgroundScheduler(executor=_executor)

    # Barrido diario de reglas de negocio
    scheduler.add_job(
        _run_commercial_check_sync,
        trigger=IntervalTrigger(hours=24),
        args=[session_factory],
        id="commercial_check_daily",
        name="Verificación comercial diaria",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Monitor de análisis periódico (cada 15 minutos)
    scheduler.add_job(
        _run_analysis_monitor_sync,
        trigger=IntervalTrigger(minutes=ANALYSIS_MONITOR_INTERVAL_MINUTES),
        args=[session_factory],
        id="analysis_monitor",
        name="Monitor de análisis de fuentes",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Marcar el pipeline como activo (R-X03)
    pipeline_state.mark_active()

    scheduler.start()
    logger.info("✅ APScheduler iniciado — barrido diario y monitor de análisis configurados")
    return scheduler


def stop_scheduler() -> None:
    """Detiene el scheduler liberando recursos."""
    global scheduler, _executor

    if scheduler:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("APScheduler detenido")

    if _executor:
        _executor.shutdown(wait=False)
        _executor = None
