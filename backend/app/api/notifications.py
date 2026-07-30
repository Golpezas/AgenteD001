"""
Endpoint de Notificaciones — API /api/v1/notifications.

Proporciona listado paginado con filtros, marcado como leído
(individual y masivo), creación manual y verificación comercial.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.notification import (
    NotificationCreate,
    NotificationList,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=NotificationList)
async def list_notifications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    type: str | None = Query(None, description="Filtrar por tipo: system, business, manual"),
    category: str | None = Query(None, description="Filtrar por categoría"),
    is_read: bool | None = Query(None, description="Filtrar por estado de lectura"),
    db: AsyncSession = Depends(get_db),
):
    """Lista notificaciones con paginación y filtros opcionales."""
    service = NotificationService(db)

    filters = {}
    if type is not None:
        filters["type"] = type
    if category is not None:
        filters["category"] = category
    if is_read is not None:
        filters["is_read"] = is_read

    result = await service.notification_repo.get_all(
        page=page,
        per_page=per_page,
        filters=filters if filters else None,
    )

    return NotificationList(**result)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
):
    """Retorna la cantidad de notificaciones no leídas."""
    service = NotificationService(db)
    count = await service.get_unread_count()
    return UnreadCountResponse(count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Marca una notificación como leída."""
    service = NotificationService(db)
    notification = await service.mark_as_read(notification_id)
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada",
        )
    return notification


@router.patch("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
):
    """Marca todas las notificaciones no leídas como leídas."""
    service = NotificationService(db)
    updated = await service.mark_all_read()
    return {"updated": updated}


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: NotificationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crea una notificación manual (type=manual)."""
    service = NotificationService(db)
    notification = await service.create_notification(
        type=payload.type,
        category=payload.category,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
    )
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la notificación",
        )
    return notification


@router.post("/force-check")
async def force_commercial_check(
    db: AsyncSession = Depends(get_db),
):
    """Ejecuta verificación comercial manual."""
    service = NotificationService(db)
    created = await service.force_commercial_check()
    return {"created": created}
