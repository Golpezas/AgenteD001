"""
Configuración async de Alembic — SQLAlchemy 2.0 + asyncpg.

Utiliza run_async para ejecutar migraciones con el motor asíncrono.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.models.base import Base

# Importar todos los modelos para que autogenerate los detecte
from app.models.company import Company  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.price_list import PriceList, PriceListItem  # noqa: F401
from app.models.pricing_rule import PricingRule  # noqa: F401

# Configuración de logging desde alembic.ini
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata objetivo para autogenerate
target_metadata = Base.metadata

# URL de conexión desde settings (no desde alembic.ini)
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """
    Ejecuta migraciones en modo 'offline'.

    Las sentencias SQL se generan sin conexión a la base de datos.
    Útil para revisar el SQL antes de ejecutarlo.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Ejecuta las migraciones sobre una conexión dada."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Ejecuta migraciones en modo 'online' con motor asíncrono.

    Crea un engine desde la configuración y ejecuta las migraciones
    dentro de una conexión asíncrona.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.database_url
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Ejecuta migraciones en modo 'online'.

    Wrapper que corre la función asíncrona en el event loop.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
