"""
Endpoint manual para ejecutar seed data.

Útil en free tier de Render donde no hay Jobs ni Shell.
Llamar con:
    curl -X POST https://agented-backend.onrender.com/api/v1/seed
"""

import logging

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.database import engine
from seed.seed_data import seed_todo

logger = logging.getLogger("uvicorn")
router = APIRouter(prefix="/api/v1", tags=["seed"])


@router.post("/seed")
async def run_seed():
    """Ejecuta seed data (idempotente)."""
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_factory() as session:
        counts = await seed_todo(session)

    return {
        "message": "Seed completado",
        "factores": counts["factores"],
        "politicas": counts["politicas"],
        "productos": counts["productos"],
        "price_list": counts["price_list"]["price_list"],
        "items": counts["price_list"]["items"],
    }
