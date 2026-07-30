"""Schemas Pydantic v2 — DTOs de entrada/salida."""

from app.schemas.analysis import (
    AnalysisJobCreate,
    AnalysisJobList,
    AnalysisJobResponse,
    AnalysisJobUpdate,
    AnalysisProposal,
    AnalysisResultCreate,
    AnalysisResultList,
    AnalysisResultResponse,
    AnalysisResultUpdate,
    ScreenshotResult,
)
from app.schemas.business_policy import (
    BusinessPolicyCreate,
    BusinessPolicyList,
    BusinessPolicyResponse,
    BusinessPolicyUpdate,
)
from app.schemas.calculation_factor import (
    CalculationFactorCreate,
    CalculationFactorList,
    CalculationFactorResponse,
    CalculationFactorUpdate,
)
from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.company import CompanyCreate, CompanyList, CompanyResponse, CompanyUpdate
from app.schemas.notification import (
    NotificationCreate,
    NotificationList,
    NotificationResponse,
    UnreadCountResponse,
)
from app.schemas.price_list import PriceListCreate, PriceListResponse
from app.schemas.price_list_item import PriceListItemCreate, PriceListItemResponse
from app.schemas.pricing_rule import PricingRuleCreate, PricingRuleResponse
from app.schemas.product import ProductCreate, ProductList, ProductResponse, ProductUpdate

__all__ = [
    "AnalysisJobCreate",
    "AnalysisJobList",
    "AnalysisJobResponse",
    "AnalysisJobUpdate",
    "AnalysisProposal",
    "AnalysisResultCreate",
    "AnalysisResultList",
    "AnalysisResultResponse",
    "AnalysisResultUpdate",
    "ScreenshotResult",
    "BusinessPolicyCreate",
    "BusinessPolicyList",
    "BusinessPolicyResponse",
    "BusinessPolicyUpdate",
    "NotificationCreate",
    "NotificationList",
    "NotificationResponse",
    "UnreadCountResponse",
    "CalculationFactorCreate",
    "CalculationFactorList",
    "CalculationFactorResponse",
    "CalculationFactorUpdate",
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
