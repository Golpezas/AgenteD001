"""
Configuración de pytest — fixtures asíncronos para pruebas con SQLAlchemy.

Provee una sesión de base de datos aislada por test usando
savepoints dentro de una transacción externa.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.models.base import Base

# Base de datos archivo para tests (no en memoria para evitar problemas con aiosqlite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Crea un event loop para toda la sesión de tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_engine():
    """Crea el motor asíncrono de pruebas."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine) -> AsyncSession:
    """
    Provee una sesión aislada por test.

    Usa una conexión con transacción externa + savepoint para que
    los commits dentro del test sean reversibles al finalizar.
    """
    connection = await async_engine.connect()
    transaction = await connection.begin()

    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
    )

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()
