"""
Aplicación FastAPI principal — AgenteD Backend.

Configura lifespan (migraciones automáticas), CORS,
e incluye todos los routers de la API.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


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
        import asyncio
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("script_location", "alembic")
        # Ejecutar en un thread separado para no bloquear
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, command.upgrade, alembic_cfg, "head")
    except Exception:
        # Si falla la migración, la app igual arranca (degradada)
        pass

    yield

    # Shutdown: limpieza si es necesaria
    pass


app = create_app()
