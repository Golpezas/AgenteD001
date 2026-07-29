"""Schemas Pydantic v2 — DTOs de entrada/salida."""

from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyList
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductList
from app.schemas.price_list import PriceListCreate, PriceListResponse
from app.schemas.price_list_item import PriceListItemCreate, PriceListItemResponse
from app.schemas.pricing_rule import PricingRuleCreate, PricingRuleResponse
from app.schemas.common import PaginatedResponse, ErrorResponse

__all__ = [
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyResponse",
    "CompanyList",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductList",
    "PriceListCreate",
    "PriceListResponse",
    "PriceListItemCreate",
    "PriceListItemResponse",
    "PricingRuleCreate",
    "PricingRuleResponse",
    "PaginatedResponse",
    "ErrorResponse",
]
