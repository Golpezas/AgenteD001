"""
Aplicación FastAPI principal — AgenteD Backend.

Configura lifespan (migraciones automáticas), CORS,
e incluye todos los routers de la API.
"""

import asyncio
import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

    # ── Global exception handler ──────────────────────────────────
    # Atrapa ANY exception para que Starlette NO devuelva un 500
    # plano (text/plain) que bypassea CORSMiddleware. En vez de eso,
    # retorna JSON con el error real y logs para debugging.
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception on %s %s\n%s",
            request.method,
            request.url.path,
            traceback.format_exc(),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {type(exc).__name__}: {exc}"},
        )

    # Incluir routers
    from app.api.health import router as health_router
    from app.api.clients import router as clients_router
    from app.api.products import router as products_router
    from app.api.pixelrag import router as pixelrag_router
    from app.api.calculation_factors import router as calculation_factors_router
    from app.api.business_policies import router as business_policies_router

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(clients_router)
    app.include_router(products_router)
    app.include_router(pixelrag_router)
    app.include_router(calculation_factors_router)
    app.include_router(business_policies_router)

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan de la aplicación.

    Ejecuta migraciones de Alembic al iniciar el backend.
    """
    # Startup: ejecutar migraciones
    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("script_location", "migrations")
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
