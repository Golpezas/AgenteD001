"""
Configuración de la base de datos — SQLAlchemy 2.0 asíncrono.

Define el motor asíncrono, la fábrica de sesiones y la dependencia
de inyección para FastAPI.
"""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from typing import AsyncGenerator

from app.core.config import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=(settings.environment == "development"),
    pool_size=10,
    max_overflow=20,
)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI que provee una sesión asíncrona por request.

    Se cierra automáticamente al finalizar el manejo del request.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
