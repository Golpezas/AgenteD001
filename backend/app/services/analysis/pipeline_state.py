"""
Registry de estado del pipeline de análisis (R-X03).

Singleton a nivel de módulo: el scheduler (mark_active) y el
orchestrator (mark_success) escriben el estado; el endpoint
GET /api/v1/pixelrag/test lo expone cuando el pipeline está registrado.
"""

from datetime import datetime
from typing import Optional


class AnalysisPipelineState:
    """Estado del pipeline de análisis para el health check (R-X03)."""

    def __init__(self) -> None:
        self.active: bool = False
        self.last_successful_run: Optional[datetime] = None

    def mark_active(self) -> None:
        """Marca el pipeline como activo (job de monitoreo registrado)."""
        self.active = True

    def mark_success(self, when: Optional[datetime] = None) -> None:
        """Registra la última ejecución exitosa del pipeline."""
        self.last_successful_run = when or datetime.now()

    def is_registered(self) -> bool:
        """El pipeline está registrado si fue activado o tuvo una ejecución exitosa."""
        return self.active or self.last_successful_run is not None

    def snapshot(self) -> Optional[dict]:
        """Retorna el estado del pipeline, o None si no está registrado."""
        if not self.is_registered():
            return None
        return {
            "active": self.active,
            "last_successful_run": (
                self.last_successful_run.isoformat()
                if self.last_successful_run is not None
                else None
            ),
        }


pipeline_state = AnalysisPipelineState()
