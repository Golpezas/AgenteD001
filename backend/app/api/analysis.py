"""
API de Análisis — endpoints /api/v1/analysis.

W-3: CRUD de ScrapedSource (POST /sources, GET /sources, DELETE /sources/{id}).
W-4: jobs, results y approve/reject.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.analysis import ScrapedSourceRepository
from app.schemas.analysis import (
    ScrapedSourceCreate,
    ScrapedSourceList,
    ScrapedSourceResponse,
)
from app.services.analysis.url_guard import validate_external_url

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.post(
    "/sources",
    response_model=ScrapedSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_source(
    payload: ScrapedSourceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Registers a scraped source (409 if the url already exists).

    The URL is validated by the SSRF guard (D7) BEFORE any lookup or insert;
    private/loopback/link-local/metadata targets and non-http schemes get 400.
    """
    try:
        await validate_external_url(payload.url)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    repo = ScrapedSourceRepository(db)

    existing = await repo.get_by_url(payload.url)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Source with url '{payload.url}' already exists",
        )

    source = await repo.create(payload.model_dump())
    return source


@router.get("/sources", response_model=ScrapedSourceList)
async def list_sources(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lista paginada de fuentes scrapeadas activas."""
    repo = ScrapedSourceRepository(db)
    result = await repo.get_all(page=page, per_page=per_page)
    return ScrapedSourceList(**result)


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Elimina lógicamente una fuente scrapeada (404 si no existe)."""
    repo = ScrapedSourceRepository(db)
    deleted = await repo.soft_delete(source_id)
    if deleted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )
    return None
