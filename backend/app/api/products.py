"""
Endpoint de Productos — CRUD /api/v1/products.

Implementa el patrón Service Layer inyectado en cada endpoint.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate, ProductList
from app.services.product import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crea un nuevo producto."""
    service = ProductService(db)
    product = await service.create(payload.model_dump())
    return product


@router.get("", response_model=ProductList)
async def list_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    family: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Lista productos con paginación y filtro opcional por familia."""
    service = ProductService(db)

    if family:
        result = await service.get_by_family(family, page=page, per_page=per_page)
    else:
        result = await service.get_all(page=page, per_page=per_page)

    return ProductList(**result)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene un producto por ID."""
    service = ProductService(db)
    product = await service.get_with_prices(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un producto existente."""
    service = ProductService(db)
    product = await service.update(product_id, payload.model_dump(exclude_unset=True))
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.delete("/{product_id}", response_model=ProductResponse)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Elimina (soft delete) un producto."""
    service = ProductService(db)
    product = await service.deactivate(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product
