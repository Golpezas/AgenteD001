"""
Endpoint de Políticas Comerciales — GET /api/v1/business-policies.

Lista filtrable de políticas: descuentos, beneficios, financiamiento y reglas.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.business_policy import BusinessPolicyList, BusinessPolicyResponse
from app.services.business_policy import BusinessPolicyService

router = APIRouter(prefix="/api/v1/business-policies", tags=["business-policies"])


@router.get("/active", response_model=BusinessPolicyList)
async def list_active_policies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lista políticas comerciales actualmente vigentes.

    Aplica filtros de vigencia: effective_from <= hoy <= effective_to,
    y excluye políticas inactivas.
    """
    service = BusinessPolicyService(db)
    result = await service.get_active(page=page, per_page=per_page)
    return BusinessPolicyList(**result)


@router.get("", response_model=BusinessPolicyList)
async def list_business_policies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    policy_type: str | None = Query(None),
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Lista políticas comerciales con paginación y filtros.

    - `policy_type`: Filtrar por tipo (discount, benefit, financing, policy).
    - `is_active`: Filtrar por estado activo/inactivo.
    """
    service = BusinessPolicyService(db)

    if policy_type:
        result = await service.get_by_type(policy_type, page=page, per_page=per_page)
    elif is_active is not None:
        filters = {} if is_active else {"is_active": is_active}
        result = await service.get_all(page=page, per_page=per_page, filters=filters or None)
    else:
        result = await service.get_all(page=page, per_page=per_page)

    return BusinessPolicyList(**result)


@router.get("/{policy_id}", response_model=BusinessPolicyResponse)
async def get_business_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene una política comercial por ID."""
    service = BusinessPolicyService(db)
    policy = await service.get_by_id(policy_id)
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Política no encontrada",
        )
    return policy
