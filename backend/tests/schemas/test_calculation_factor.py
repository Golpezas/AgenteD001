"""
Tests para schemas de CalculationFactor — validación de Pydantic.
"""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.calculation_factor import (
    CalculationFactorCreate,
    CalculationFactorList,
    CalculationFactorResponse,
    CalculationFactorUpdate,
)


class TestCalculationFactorSchema:
    """Suite de tests para los schemas de CalculationFactor."""

    def test_create_valid(self):
        """Debe crear un schema con todos los campos obligatorios."""
        data = CalculationFactorCreate(
            concept_key="accesos_simultaneos",
            concept_name="Accesos Simultáneos",
            technology_tier="Express",
            factor=5.0,
        )
        assert data.concept_key == "accesos_simultaneos"
        assert data.concept_name == "Accesos Simultáneos"
        assert data.technology_tier == "Express"
        assert data.factor == 5.0
        assert data.is_available is None  # optional, defaults to None
        assert data.extra_data is None

    def test_create_without_factor(self):
        """factor debe ser opcional (NULL = requires_quote)."""
        data = CalculationFactorCreate(
            concept_key="horas_dba",
            concept_name="Horas DBA",
            technology_tier="Premium",
        )
        assert data.factor is None

    def test_create_with_extra_data(self):
        """Debe aceptar metadata opcional."""
        data = CalculationFactorCreate(
            concept_key="test",
            concept_name="Test",
            technology_tier="Advanced",
            extra_data={"requires_quote": True},
        )
        assert data.extra_data == {"requires_quote": True}

    def test_create_empty_concept_key_raises(self):
        """Debe rechazar concept_key vacío."""
        with pytest.raises(ValidationError):
            CalculationFactorCreate(
                concept_key="",
                concept_name="Test",
                technology_tier="Express",
            )

    def test_create_factor_negative(self):
        """Debe aceptar factor negativo."""
        data = CalculationFactorCreate(
            concept_key="penalizacion",
            concept_name="Penalización",
            technology_tier="Premium",
            factor=-1.0,
        )
        assert data.factor == -1.0

    def test_response_from_attributes(self):
        """Response debe tener from_attributes configurado."""
        assert CalculationFactorResponse.model_config.get("from_attributes") is True

    def test_response_fields(self):
        """Response debe incluir todos los campos del modelo."""
        now = datetime.now()
        uid = uuid4()
        data = CalculationFactorResponse(
            id=uid,
            concept_key="accesos_simultaneos",
            concept_name="Accesos Simultáneos",
            technology_tier="Express",
            factor=5.0,
            is_available=True,
            extra_data=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert data.id == uid
        assert data.factor == 5.0
        assert data.is_active is True

    def test_list_pagination(self):
        """List debe contener items, total, page y per_page."""
        now = datetime.now()
        uid = uuid4()
        item = CalculationFactorResponse(
            id=uid,
            concept_key="test",
            concept_name="Test",
            technology_tier="Express",
            is_available=True,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        data = CalculationFactorList(items=[item], total=1, page=1, per_page=10)
        assert len(data.items) == 1
        assert data.total == 1
        assert data.page == 1
        assert data.per_page == 10


class TestCalculationFactorUpdateSchema:
    """Suite de tests para CalculationFactorUpdate."""

    def test_update_partial(self):
        """Debe permitir actualización parcial."""
        data = CalculationFactorUpdate(factor=3.0)
        assert data.factor == 3.0
        assert data.concept_key is None
        assert data.concept_name is None
