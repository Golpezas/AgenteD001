"""
Aplicación FastAPI principal — AgenteD Backend.

Configura lifespan (migraciones automáticas), CORS,
e incluye todos los routers de la API.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from alembic.config import Config
from alembic import command

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

logger = logging.getLogger("uvicorn")


def create_app() -> FastAPI:
    """Crea y configura la instancia de FastAPI."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Incluir routers
    from app.api.health import router as health_router
    from app.api.clients import router as clients_router
    from app.api.products import router as products_router
    from app.api.pixelrag import router as pixelrag_router

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(clients_router)
    app.include_router(products_router)
    app.include_router(pixelrag_router)

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan de la aplicación.

    Ejecuta migraciones de Alembic al iniciar el backend.
    """
    # Startup: ejecutar migraciones
    try:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("script_location", "alembic")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, command.upgrade, alembic_cfg, "head")
        logger.info("✅ Migraciones ejecutadas correctamente")
    except Exception as e:
        import traceback
        logger.error(f"❌ Migraciones fallaron: {e}\n{traceback.format_exc()}")
        # La app igual arranca (degradada)

    yield

    # Shutdown: limpieza si es necesaria
    pass


app = create_app()
