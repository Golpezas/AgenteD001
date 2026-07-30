"""
Endpoint de Factores de Licenciamiento — GET /api/v1/calculation-factors.

Lista filtrable de factores multiplicadores por concepto y technology tier.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.calculation_factor import CalculationFactorList, CalculationFactorResponse
from app.services.calculation_factor import CalculationFactorService

router = APIRouter(prefix="/api/v1/calculation-factors", tags=["calculation-factors"])


@router.get("", response_model=CalculationFactorList)
async def list_calculation_factors(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    technology_tier: str | None = Query(None),
    include_unavailable: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Lista factores de licenciamiento con paginación y filtros.

    - `technology_tier`: Filtrar por tier (Express, Advanced, Premium).
    - `include_unavailable`: Incluir factores marcados como no disponibles.
    """
    service = CalculationFactorService(db)
    result = await service.get_all(
        page=page,
        per_page=per_page,
        technology_tier=technology_tier,
        include_unavailable=include_unavailable,
    )
    return CalculationFactorList(**result)


@router.get("/{concept_key}", response_model=CalculationFactorResponse)
async def get_calculation_factor(
    concept_key: str,
    technology_tier: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Obtiene un factor por concept_key.

    Si se especifica `technology_tier`, busca la combinación exacta.
    Si no, retorna el primer factor disponible para ese concept_key.
    """
    service = CalculationFactorService(db)

    if technology_tier:
        factor = await service.get_by_concept_and_tier(concept_key, technology_tier)
    else:
        result = await service.get_all(
            page=1,
            per_page=1,
            filters={"concept_key": concept_key},
            include_unavailable=False,
        )
        items = result["items"]
        factor = items[0] if items else None

    if factor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Factor '{concept_key}' no encontrado",
        )
    return factor
