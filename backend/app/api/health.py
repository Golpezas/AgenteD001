"""
Endpoint de health check — GET /api/v1/health.

Retorna el estado del sistema, versión y conectividad
con la base de datos.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check del sistema.

    Retorna estado 200 siempre, con detalles de conectividad.
    """
    db_status = "disconnected"
    overall_status = "ok"

    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        overall_status = "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
