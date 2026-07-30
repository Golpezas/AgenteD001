"""
Tests de integración — verifica que los servicios CRUD inyectan
NotificationService correctamente y que errores no interrumpen el CRUD.

Cubre los escenarios de R-NB04:
- Notificación al crear producto
- Notificación al actualizar cliente
- Notificación al desactivar política
- Error en notificación no interrumpe CRUD
- Notificación al actualizar precio
"""

from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.product import Product
from app.models.company import Company
from app.models.business_policy import BusinessPolicy
from app.models.price_list import PriceList
from app.models.price_list import PriceListItem
from app.services.product import ProductService
from app.services.company import CompanyService
from app.services.business_policy import BusinessPolicyService
from app.services.price_list_item import PriceListItemService


class TestNotificationIntegration:
    """Suite de integración: servicios CRUD → NotificationService."""

    # ── Helpers ─────────────────────────────────────────────

    async def _count_notifications(self, db_session: AsyncSession) -> int:
        result = await db_session.execute(select(Notification))
        return len(result.scalars().all())

    async def _find_notifications(
        self, db_session: AsyncSession, **filters,
    ) -> list[Notification]:
        query = select(Notification)
        for key, value in filters.items():
            column = getattr(Notification, key, None)
            if column is not None:
                query = query.where(column == value)
        result = await db_session.execute(query)
        return list(result.scalars().all())

    # ── Tests ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_create_product_creates_notification(
        self, db_session: AsyncSession,
    ):
        """Crear producto debe generar Notification tipo system."""
        service = ProductService(db_session)

        product = await service.create({
            "code": "NOTIF-PROD-001",
            "name": "Producto Test Notif",
        })
        assert product is not None

        notifs = await self._find_notifications(
            db_session,
            type="system",
            resource_type="product",
            resource_id=str(product.id),
        )
        assert len(notifs) == 1
        n = notifs[0]
        assert n.title == "Producto creado: Producto Test Notif"
        assert n.category == "product"
        assert n.severity == "success"
        assert n.is_read is False

    @pytest.mark.asyncio
    async def test_update_company_creates_notification(
        self, db_session: AsyncSession,
    ):
        """Actualizar cliente debe generar Notification tipo system."""
        service = CompanyService(db_session)

        company = await service.create({
            "business_name": "Empresa Original SRL",
            "email": "original@test.com",
        })
        assert company is not None

        updated = await service.update(company.id, {"email": "nuevo@test.com"})
        assert updated is not None

        notifs = await self._find_notifications(
            db_session,
            type="system",
            resource_type="company",
            resource_id=str(company.id),
        )
        # Debería haber 2: una de create y una de update
        assert len(notifs) == 2

        update_notif = next(n for n in notifs if n.title.startswith("Cliente actualizado"))
        assert update_notif.title == "Cliente actualizado: Empresa Original SRL"
        assert update_notif.category == "company"
        assert update_notif.severity == "info"

    @pytest.mark.asyncio
    async def test_deactivate_policy_creates_notification(
        self, db_session: AsyncSession,
    ):
        """Desactivar política debe generar Notification tipo system."""
        service = BusinessPolicyService(db_session)

        policy = await service.create({
            "name": "Política a eliminar",
            "policy_type": "discount",
        })
        assert policy is not None

        deactivated = await service.deactivate(policy.id)
        assert deactivated is not None
        assert deactivated.is_active is False

        notifs = await self._find_notifications(
            db_session,
            type="system",
            resource_type="business_policy",
            resource_id=str(policy.id),
        )
        # Debería haber 2: una de create y una de deactivate
        assert len(notifs) == 2

        deactivate_notif = next(
            n for n in notifs if n.title.startswith("Política eliminada")
        )
        assert deactivate_notif.title == "Política eliminada: Política a eliminar"
        assert deactivate_notif.category == "policy"
        assert deactivate_notif.severity == "warning"

    @pytest.mark.asyncio
    async def test_notification_error_does_not_interrupt_crud(
        self, db_session: AsyncSession,
    ):
        """Error en NotificationService NO debe interrumpir el CRUD.

        Se mockea NotificationService para que lance excepción
        al instanciarse. El CRUD debe completarse sin error.
        """
        # Contar notificaciones antes para verificar que no se crearon
        count_before = await self._count_notifications(db_session)

        with patch(
            "app.services.product.NotificationService",
            side_effect=Exception("Notificaciones fuera de servicio"),
        ):
            service = ProductService(db_session)
            product = await service.create({
                "code": "ERR-NOTIF-001",
                "name": "Producto sin notificación",
            })

        # El producto debe haberse creado correctamente
        assert product is not None
        assert product.name == "Producto sin notificación"
        assert product.code == "ERR-NOTIF-001"
        assert product.is_active is True

        # Y NO debe haber notificaciones nuevas
        count_after = await self._count_notifications(db_session)
        assert count_after == count_before

    @pytest.mark.asyncio
    async def test_update_price_creates_notification(
        self, db_session: AsyncSession,
    ):
        """Actualizar precio debe generar Notification tipo system.

        Requiere crear Product y PriceList primero (relaciones
        necesarias de PriceListItem).
        """
        # Crear producto
        prod_service = ProductService(db_session)
        product = await prod_service.create({
            "code": "PRICE-NOTIF-001",
            "name": "Producto para precio",
        })
        assert product is not None

        # Crear lista de precios
        price_list = PriceList(name="Lista Test Precios")
        db_session.add(price_list)
        await db_session.commit()
        await db_session.refresh(price_list)

        # Crear ítem de precio
        item_service = PriceListItemService(db_session)
        from datetime import date

        item = await item_service.create({
            "product_id": product.id,
            "price_list_id": price_list.id,
            "price": 1000.00,
            "currency": "ARS",
            "effective_from": date(2025, 1, 1),
        })
        assert item is not None

        # Actualizar precio
        updated = await item_service.update(item.id, {"price": 1200.00})
        assert updated is not None
        assert float(updated.price) == 1200.00

        # Buscar notificaciones con resource_type=price_list_item
        notifs = await self._find_notifications(
            db_session,
            type="system",
            resource_type="price_list_item",
        )

        # Debería haber al menos 2: create + update
        assert len(notifs) >= 2

        update_notifs = [
            n for n in notifs if n.title.startswith("Precio actualizado")
        ]
        assert len(update_notifs) == 1
        assert (
            update_notifs[0].title
            == "Precio actualizado: Producto para precio"
        )
        assert update_notifs[0].category == "price"
        assert update_notifs[0].severity == "info"

    @pytest.mark.asyncio
    async def test_deactivate_price_creates_notification(
        self, db_session: AsyncSession,
    ):
        """Desactivar precio debe generar notificación 'Precio eliminado'."""
        prod_service = ProductService(db_session)
        product = await prod_service.create({
            "code": "PRICE-DEL-001",
            "name": "Producto precio eliminar",
        })

        price_list = PriceList(name="Lista Eliminación")
        db_session.add(price_list)
        await db_session.commit()
        await db_session.refresh(price_list)

        from datetime import date

        item_service = PriceListItemService(db_session)
        item = await item_service.create({
            "product_id": product.id,
            "price_list_id": price_list.id,
            "price": 500.00,
            "currency": "ARS",
            "effective_from": date(2025, 1, 1),
        })

        deactivated = await item_service.deactivate(item.id)
        assert deactivated is not None
        assert deactivated.is_active is False

        notifs = await self._find_notifications(
            db_session,
            type="system",
            resource_type="price_list_item",
            resource_id=str(item.id),
        )

        deactivate_notifs = [
            n for n in notifs if n.title == "Precio eliminado"
        ]
        assert len(deactivate_notifs) == 1
        assert deactivate_notifs[0].severity == "warning"
        assert deactivate_notifs[0].category == "price"
