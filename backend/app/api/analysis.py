"""
API de Análisis — endpoints /api/v1/analysis.

W-3: CRUD de ScrapedSource (POST /sources, GET /sources, DELETE /sources/{id}).
W-4: jobs (POST/GET /jobs, GET /jobs/{id}), results (GET /results) y
     approve/reject, con BackgroundTasks y session factory inyectable.

Wiring de BackgroundTasks: la bg task NO reusa la sesión de Depends(get_db)
(se cierra al terminar el request) → abre su propia AsyncSession desde
`async_session` (nivel de módulo, inyectable en tests) y arma el
orchestrator vía `build_orchestrator` (nivel de módulo, mockeable).
"""

from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session, get_db
from app.repositories.analysis import (
    AnalysisJobRepository,
    AnalysisResultRepository,
    ScrapedSourceRepository,
)
from app.schemas.analysis import (
    AnalysisJobCreate,
    AnalysisJobList,
    AnalysisJobResponse,
    AnalysisResultList,
    RejectAnalysisRequest,
    ScrapedSourceCreate,
    ScrapedSourceList,
    ScrapedSourceResponse,
)
from app.services.analysis.url_guard import validate_external_url
from app.services.analysis.gemini_client import GeminiClient
from app.services.analysis.orchestrator import AnalysisOrchestrator
from app.services.analysis.scraper import WebScraper
from app.services.notification import NotificationService
from app.services.pixelrag import PixelRAGService

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])

# D4/D7 limits enforced at the API boundary, before any job is created.
MAX_IMAGE_BYTES_BASE64 = 8 * 1024 * 1024  # base64 payload cap (~6 MiB decoded)
MAX_URL_CHARS = 2048


def build_orchestrator(session: AsyncSession) -> AnalysisOrchestrator:
    """Factory de AnalysisOrchestrator con servicios reales (punto de mockeo)."""
    return AnalysisOrchestrator(
        job_repo=AnalysisJobRepository(session),
        result_repo=AnalysisResultRepository(session),
        source_repo=ScrapedSourceRepository(session),
        gemini_client=GeminiClient(),
        scraper=WebScraper(),
        pixelrag=PixelRAGService(),
        notification_service=NotificationService(session),
    )


async def _process_job_task(job_id: UUID) -> None:
    """Procesa un job en background con su propia sesión."""
    async with async_session() as session:
        orchestrator = build_orchestrator(session)
        await orchestrator.process_job(job_id)


# ── ScrapedSources (W-3) ───────────────────────────────


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


# ── Jobs y Results (W-4) ───────────────────────────────


@router.post(
    "/jobs",
    response_model=AnalysisJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_job(
    payload: AnalysisJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Creates an analysis job and schedules background processing (202).

    Enforces the D4/D7 limits before any job is created: image jobs require a
    base64 ``image_bytes`` string of at most 8 MiB (413 when exceeded), url
    jobs require a ``url`` string of at most 2048 chars validated by the SSRF
    guard (400 for private/loopback targets or non-http schemes).
    """
    job_type = payload.job_type
    input_data = payload.input_data or {}

    if job_type not in ("image", "url"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job_type '{job_type}'. Must be 'image' or 'url'",
        )

    if job_type == "image":
        image_bytes = input_data.get("image_bytes")
        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="job_type 'image' requires 'image_bytes' in input_data",
            )
        if not isinstance(image_bytes, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="input_data.image_bytes must be a base64 string",
            )
        if len(image_bytes) > MAX_IMAGE_BYTES_BASE64:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    "input_data.image_bytes exceeds the "
                    f"{MAX_IMAGE_BYTES_BASE64} characters limit"
                ),
            )
    elif job_type == "url":
        url = input_data.get("url")
        if not url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="job_type 'url' requires 'url' in input_data",
            )
        if not isinstance(url, str) or len(url) > MAX_URL_CHARS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"input_data.url must be a string of at most {MAX_URL_CHARS} chars",
            )
        try:
            await validate_external_url(url)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

    repo = AnalysisJobRepository(db)
    job = await repo.create(
        {
            "job_type": job_type,
            "input_data": input_data,
            "status": "pending",
        }
    )

    background_tasks.add_task(_process_job_task, job.id)
    return job


@router.get("/jobs", response_model=AnalysisJobList)
async def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    """Lista paginada de jobs de análisis (filtro opcional por status)."""
    repo = AnalysisJobRepository(db)
    filters = {"status": status_filter} if status_filter else None
    result = await repo.get_all(page=page, per_page=per_page, filters=filters)
    return AnalysisJobList(**result)


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Estado de un job (404 si no existe)."""
    orchestrator = build_orchestrator(db)
    status_info = await orchestrator.get_job_status(job_id)
    if status_info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return status_info


@router.get("/results", response_model=AnalysisResultList)
async def list_results(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    """Lista paginada de resultados de análisis (filtro opcional por status)."""
    repo = AnalysisResultRepository(db)
    filters = {"status": status_filter} if status_filter else None
    result = await repo.get_all(page=page, per_page=per_page, filters=filters)
    return AnalysisResultList(**result)


@router.post("/results/{result_id}/approve")
async def approve_result(
    result_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Aprueba una propuesta (404 inexistente; 409 ya resuelta)."""
    result_repo = AnalysisResultRepository(db)
    result = await result_repo.get_by_id(result_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found",
        )
    if result.status != "proposal":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Result already resolved (status={result.status})",
        )

    orchestrator = build_orchestrator(db)
    ok = await orchestrator.approve_proposal(result_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve result",
        )
    return {"id": str(result_id), "status": "accepted"}


@router.post("/results/{result_id}/reject")
async def reject_result(
    result_id: UUID,
    payload: RejectAnalysisRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Rechaza una propuesta con motivo opcional (404 inexistente; 409 ya resuelta)."""
    result_repo = AnalysisResultRepository(db)
    result = await result_repo.get_by_id(result_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found",
        )
    if result.status != "proposal":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Result already resolved (status={result.status})",
        )

    reason = payload.reason if payload else None
    orchestrator = build_orchestrator(db)
    ok = await orchestrator.reject_proposal(result_id, reason or "")
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject result",
        )
    return {"id": str(result_id), "status": "rejected", "reason": reason}
