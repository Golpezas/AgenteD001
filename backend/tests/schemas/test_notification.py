"""
Tests para schemas de Notification — validación Pydantic v2.
"""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.notification import (
    NotificationCreate,
    NotificationList,
    NotificationResponse,
    UnreadCountResponse,
)


class TestNotificationCreateSchema:
    """Suite para NotificationCreate."""

    def test_valid_notification_create(self):
        """Debe aceptar un payload válido completo."""
        data = {
            "type": "system",
            "category": "product",
            "title": "Producto creado",
            "description": "Producto creado exitosamente",
            "severity": "info",
            "resource_type": "product",
            "resource_id": str(uuid.uuid4()),
        }
        schema = NotificationCreate(**data)
        assert schema.type == "system"
        assert schema.category == "product"
        assert schema.title == "Producto creado"
        assert schema.description == "Producto creado exitosamente"
        assert schema.severity == "info"

    def test_notification_create_minimal(self):
        """Debe aceptar solo campos obligatorios."""
        data = {
            "type": "business",
            "category": "commercial",
            "title": "Alerta comercial",
        }
        schema = NotificationCreate(**data)
        assert schema.type == "business"
        assert schema.severity == "info"  # default

    def test_notification_create_invalid_type(self):
        """Debe rechazar type inválido."""
        with pytest.raises(ValidationError):
            NotificationCreate(
                type="invalid_type",
                category="test",
                title="Test",
            )

    def test_notification_create_invalid_severity(self):
        """Debe rechazar severity inválido."""
        with pytest.raises(ValidationError):
            NotificationCreate(
                type="system",
                category="test",
                title="Test",
                severity="critical",
            )

    def test_notification_create_type_literal(self):
        """Debe aceptar los tres tipos válidos."""
        for t in ("system", "business", "manual"):
            schema = NotificationCreate(type=t, category="test", title="Test")
            assert schema.type == t

    def test_notification_create_severity_literal(self):
        """Debe aceptar los cuatro severity válidos."""
        for s in ("info", "warning", "error", "success"):
            schema = NotificationCreate(
                type="system",
                category="test",
                title="Test",
                severity=s,
            )
            assert schema.severity == s


class TestNotificationResponseSchema:
    """Suite para NotificationResponse."""

    def test_valid_response(self):
        """Debe construir respuesta desde atributos de modelo."""
        now = datetime.now(timezone.utc)
        data = {
            "id": uuid.uuid4(),
            "type": "system",
            "category": "product",
            "title": "Test",
            "description": None,
            "severity": "info",
            "resource_type": None,
            "resource_id": None,
            "is_read": False,
            "is_dismissed": False,
            "read_at": None,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        schema = NotificationResponse(**data)
        assert schema.id == data["id"]
        assert schema.is_read is False
        assert schema.read_at is None


class TestNotificationListSchema:
    """Suite para NotificationList."""

    def test_valid_list(self):
        """Debe construir lista paginada."""
        now = datetime.now(timezone.utc)
        items = [
            NotificationResponse(
                id=uuid.uuid4(),
                type="system",
                category="test",
                title=f"Notif {i}",
                description=None,
                severity="info",
                resource_type=None,
                resource_id=None,
                is_read=False,
                is_dismissed=False,
                read_at=None,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            for i in range(3)
        ]
        result = NotificationList(items=items, total=10, page=1, per_page=3)
        assert len(result.items) == 3
        assert result.total == 10
        assert result.page == 1
        assert result.per_page == 3


class TestUnreadCountSchema:
    """Suite para UnreadCountResponse."""

    def test_unread_count(self):
        """Debe retornar conteo correctamente."""
        schema = UnreadCountResponse(count=5)
        assert schema.count == 5

    def test_unread_count_zero(self):
        """Debe aceptar cero."""
        schema = UnreadCountResponse(count=0)
        assert schema.count == 0
