"""
Tests para Product schema — validación de family/category como Literal.
"""

import pytest
from pydantic import ValidationError

from app.schemas.product import ProductCreate, ProductUpdate


class TestProductSchemaLiteralValidation:
    """Suite de tests para validación Literal en ProductBase."""

    def test_valid_family_values(self):
        """Familia válida debe pasar la validación."""
        for family in ["Zeus", "Balcony", "MasPedidos", "Prescriptor", "CASH", "Servicios Globales"]:
            product = ProductCreate(code="TEST", name="Test", family=family)
            assert product.family == family

    def test_valid_category_values(self):
        """Categoría válida debe pasar la validación."""
        for cat in ["suscripcion", "software", "servicio", "consultoria", "capacitacion", "marketplace"]:
            product = ProductCreate(code="TEST", name="Test", category=cat)
            assert product.category == cat

    def test_invalid_family_raises_error(self):
        """Familia inválida debe lanzar ValidationError."""
        with pytest.raises(ValidationError) as exc:
            ProductCreate(code="TEST", name="Test", family="InvalidFamily")
        errors = exc.value.errors()
        assert any("family" in str(e["loc"]) for e in errors)

    def test_invalid_category_raises_error(self):
        """Categoría inválida debe lanzar ValidationError."""
        with pytest.raises(ValidationError) as exc:
            ProductCreate(code="TEST", name="Test", category="invalid_cat")
        errors = exc.value.errors()
        assert any("category" in str(e["loc"]) for e in errors)

    def test_none_family_allowed(self):
        """Family=None debe ser permitido (campo opcional)."""
        product = ProductCreate(code="TEST", name="Test")
        assert product.family is None

    def test_none_category_allowed(self):
        """Category=None debe ser permitido (campo opcional)."""
        product = ProductCreate(code="TEST", name="Test")
        assert product.category is None

    def test_product_update_valid(self):
        """ProductUpdate debe aceptar valores Literal válidos."""
        update = ProductUpdate(family="Zeus", category="software")
        assert update.family == "Zeus"
        assert update.category == "software"

    def test_product_update_invalid_family(self):
        """ProductUpdate con familia inválida debe lanzar error."""
        with pytest.raises(ValidationError):
            ProductUpdate(family="Nope")

    def test_product_update_none_family(self):
        """ProductUpdate con family=None debe ser permitido."""
        update = ProductUpdate()
        assert update.family is None
