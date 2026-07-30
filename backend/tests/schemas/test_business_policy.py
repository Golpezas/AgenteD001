"""
Tests para schemas de BusinessPolicy — validación de enum Literal.
"""

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.business_policy import (
    BusinessPolicyCreate,
    BusinessPolicyList,
    BusinessPolicyResponse,
    BusinessPolicyUpdate,
)


class TestBusinessPolicyCreateSchema:
    """Suite de tests para BusinessPolicyCreate."""

    def test_create_discount_percentage(self):
        """Debe crear un descuento porcentual."""
        data = BusinessPolicyCreate(
            name="Canal Digital",
            policy_type="discount",
            value=10.0,
            value_type="percentage",
        )
        assert data.name == "Canal Digital"
        assert data.policy_type == "discount"
        assert data.value == 10.0
        assert data.value_type == "percentage"

    def test_create_benefit(self):
        """Debe crear un beneficio."""
        data = BusinessPolicyCreate(
            name="Pago Anual Anticipado",
            policy_type="benefit",
            value=10.0,
            value_type="percentage",
        )
        assert data.policy_type == "benefit"

    def test_create_financing(self):
        """Debe crear financiamiento con condiciones."""
        data = BusinessPolicyCreate(
            name="4 pagos sin interés",
            policy_type="financing",
            conditions={"installments": 4, "interest_free": True},
        )
        assert data.policy_type == "financing"
        assert data.conditions == {"installments": 4, "interest_free": True}

    def test_create_policy_type(self):
        """Debe crear una política general."""
        data = BusinessPolicyCreate(
            name="Débito Automático Mandatorio",
            policy_type="policy",
        )
        assert data.policy_type == "policy"
        assert data.value is None

    def test_create_invalid_policy_type_raises(self):
        """Debe rechazar policy_type inválido."""
        with pytest.raises(ValidationError):
            BusinessPolicyCreate(
                name="Invalida",
                policy_type="invalid_type",
            )

    def test_create_invalid_value_type_raises(self):
        """Debe rechazar value_type inválido."""
        with pytest.raises(ValidationError):
            BusinessPolicyCreate(
                name="Test",
                policy_type="discount",
                value=10.0,
                value_type="invalid",
            )

    def test_create_with_vigencia(self):
        """Debe aceptar fechas de vigencia."""
        data = BusinessPolicyCreate(
            name="Promo",
            policy_type="benefit",
            effective_from=date(2025, 1, 1),
            effective_to=date(2025, 12, 31),
        )
        assert data.effective_from == date(2025, 1, 1)
        assert data.effective_to == date(2025, 12, 31)

    def test_create_with_client_type(self):
        """Debe aceptar client_type."""
        data = BusinessPolicyCreate(
            name="Legacy Benefit",
            policy_type="benefit",
            client_type="pre-sep-2025",
        )
        assert data.client_type == "pre-sep-2025"

    def test_create_empty_name_raises(self):
        """Debe rechazar nombre vacío."""
        with pytest.raises(ValidationError):
            BusinessPolicyCreate(
                name="",
                policy_type="discount",
            )


class TestBusinessPolicyResponseSchema:
    """Suite de tests para BusinessPolicyResponse."""

    def test_response_from_attributes(self):
        """Response debe tener from_attributes configurado."""
        assert BusinessPolicyResponse.model_config.get("from_attributes") is True

    def test_response_fields(self):
        """Response debe incluir todos los campos del modelo."""
        from datetime import datetime

        now = datetime.now()
        uid = uuid4()
        data = BusinessPolicyResponse(
            id=uid,
            name="Canal Digital",
            policy_type="discount",
            value=10.0,
            value_type="percentage",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert data.id == uid
        assert data.policy_type == "discount"
        assert data.value == 10.0


class TestBusinessPolicyListSchema:
    """Suite de tests para BusinessPolicyList."""

    def test_list_pagination(self):
        """List debe contener items, total, page y per_page."""
        from datetime import datetime

        now = datetime.now()
        uid = uuid4()
        item = BusinessPolicyResponse(
            id=uid,
            name="Test",
            policy_type="discount",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        data = BusinessPolicyList(items=[item], total=1, page=1, per_page=10)
        assert len(data.items) == 1
        assert data.total == 1


class TestBusinessPolicyUpdateSchema:
    """Suite de tests para BusinessPolicyUpdate."""

    def test_update_partial(self):
        """Debe permitir actualización parcial."""
        data = BusinessPolicyUpdate(name="New Name")
        assert data.name == "New Name"
        assert data.policy_type is None
        assert data.is_active is None

    def test_update_is_active(self):
        """Debe permitir actualizar is_active."""
        data = BusinessPolicyUpdate(is_active=False)
        assert data.is_active is False
