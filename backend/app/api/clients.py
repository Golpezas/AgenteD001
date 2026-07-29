"""
Endpoint de Clientes — CRUD /api/v1/companies.

Implementa el patrón Service Layer inyectado en cada endpoint.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate, CompanyList
from app.services.company import CompanyService

router = APIRouter(prefix="/api/v1/companies", tags=["clients"])


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crea una nueva empresa."""
    service = CompanyService(db)
    company = await service.create(payload.model_dump())
    return company


@router.get("", response_model=CompanyList)
async def list_companies(
    page: int = 1,
    per_page: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Lista empresas con paginación."""
    service = CompanyService(db)
    result = await service.get_all(page=page, per_page=per_page)
    return CompanyList(**result)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene una empresa por ID."""
    service = CompanyService(db)
    company = await service.get_by_id(company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    payload: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza una empresa existente."""
    service = CompanyService(db)
    company = await service.update(company_id, payload.model_dump(exclude_unset=True))
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.delete("/{company_id}", response_model=CompanyResponse)
async def delete_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Elimina (soft delete) una empresa."""
    service = CompanyService(db)
    company = await service.deactivate(company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company
