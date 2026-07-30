"""
Planificador de tareas periódicas — APScheduler BackgroundScheduler.

Ejecuta un barrido diario de reglas de negocio que genera
notificaciones de tipo business. Corre en un ThreadPoolExecutor
separado para no bloquear el event loop de FastAPI.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.notification import NotificationService

logger = logging.getLogger("uvicorn")

# Instancia global del scheduler
scheduler: BackgroundScheduler | None = None
_executor: ThreadPoolExecutor | None = None


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


def start_scheduler(
    session_factory: async_sessionmaker[AsyncSession],
) -> BackgroundScheduler:
    """
    Inicia el APScheduler BackgroundScheduler con el barrido diario.

    El scheduler ejecuta _run_commercial_check_sync cada 24 horas.
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

    scheduler.start()
    logger.info("✅ APScheduler iniciado — barrido diario configurado")
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
