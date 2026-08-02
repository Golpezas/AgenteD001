"""
Schemas Pydantic para Análisis de Imágenes y URLs.

Define contratos de entrada/salida para:
- AnalysisProposal (extracción Gemini Vision)
- ScreenshotResult (captura PixelRAG)
- AnalysisJob (creación, actualización, respuesta, lista)
- AnalysisResult (creación, actualización, respuesta, lista)
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Propuesta de extracción ────────────────────────────


class AnalysisProposal(BaseModel):
    """Propuesta de extracción de Gemini Vision."""

    product_name: str = Field(..., min_length=1, max_length=255)
    extracted_price: float = Field(...)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    raw_data: dict


# ── Captura de screenshot ──────────────────────────────


class ScreenshotResult(BaseModel):
    """Resultado de la captura de screenshot PixelRAG."""

    image_bytes: bytes = Field(default=b"")
    url: str = Field(..., min_length=1)
    timestamp: datetime
    resolution: tuple[int, int]


# ── Esquemas AnalysisJob ───────────────────────────────


class AnalysisJobBase(BaseModel):
    """Campos base compartidos para AnalysisJob."""

    job_type: str = Field(..., min_length=1, max_length=20)
    input_data: dict
    error_message: Optional[str] = None


class AnalysisJobCreate(AnalysisJobBase):
    """Schema para crear un job de análisis."""

    pass


class AnalysisJobUpdate(BaseModel):
    """Schema para actualizar un job (todos los campos opcionales)."""

    job_type: Optional[str] = None
    input_data: Optional[dict] = None
    status: Optional[str] = None
    result_id: Optional[UUID] = None
    error_message: Optional[str] = None


class AnalysisJobResponse(AnalysisJobBase):
    """Schema de respuesta para AnalysisJob."""

    id: UUID
    status: str
    result_id: UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisJobList(BaseModel):
    """Lista paginada de jobs de análisis."""

    items: list[AnalysisJobResponse]
    total: int
    page: int
    per_page: int

    model_config = {"from_attributes": True}


# ── Esquemas AnalysisResult ────────────────────────────


class AnalysisResultBase(BaseModel):
    """Campos base compartidos para AnalysisResult."""

    job_id: UUID
    status: Literal["proposal", "accepted", "rejected"] = "proposal"
    product_name: Optional[str] = None
    extracted_price: Optional[float] = None
    currency: Optional[str] = Field(None, max_length=3)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    raw_data: Optional[dict] = None
    proposal_data: Optional[dict] = None


class AnalysisResultCreate(AnalysisResultBase):
    """Schema para crear un resultado de análisis."""

    pass


class AnalysisResultUpdate(BaseModel):
    """Schema para actualizar un resultado (todos los campos opcionales)."""

    status: Optional[str] = None
    product_name: Optional[str] = None
    extracted_price: Optional[float] = None
    currency: Optional[str] = None
    confidence_score: Optional[float] = None
    raw_data: Optional[dict] = None
    proposal_data: Optional[dict] = None


class AnalysisResultResponse(AnalysisResultBase):
    """Schema de respuesta para AnalysisResult."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisResultList(BaseModel):
    """Lista paginada de resultados de análisis."""

    items: list[AnalysisResultResponse]
    total: int
    page: int
    per_page: int

    model_config = {"from_attributes": True}


# ── Esquemas ScrapedSource ─────────────────────────────


class ScrapedSourceCreate(BaseModel):
    """Schema para crear una fuente scrapeada.

    url es `str` validado por rango (1..2048), NO HttpUrl:
    se persiste el valor exacto sin normalización (decisión D1).
    """

    url: str = Field(..., min_length=1, max_length=2048)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    schedule_interval_minutes: Optional[int] = Field(None, ge=1)


class ScrapedSourceResponse(BaseModel):
    """Schema de respuesta para ScrapedSource."""

    id: UUID
    url: str
    name: Optional[str] = None
    schedule_interval_minutes: Optional[int] = None
    last_analyzed_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScrapedSourceList(BaseModel):
    """Lista paginada de fuentes scrapeadas."""

    items: list[ScrapedSourceResponse]
    total: int
    page: int
    per_page: int

    model_config = {"from_attributes": True}

