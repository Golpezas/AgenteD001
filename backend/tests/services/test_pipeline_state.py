"""
Tests para AnalysisPipelineState (R-X03) — registry de estado del pipeline.

RED: referencian app.services.analysis.pipeline_state, que no existe
hasta la implementación (GREEN).
"""

from datetime import datetime, timezone

import pytest

import app.services.analysis.pipeline_state as ps_module


@pytest.fixture(autouse=True)
def reset_pipeline_state():
    """Evita contaminación del singleton entre tests."""
    ps_module.pipeline_state.active = False
    ps_module.pipeline_state.last_successful_run = None
    yield
    ps_module.pipeline_state.active = False
    ps_module.pipeline_state.last_successful_run = None


class TestAnalysisPipelineState:
    """Suite de tests para el registry de estado del pipeline."""

    def test_initial_state_not_registered(self):
        """Estado inicial: inactivo, sin ejecución, NO registrado."""
        assert ps_module.pipeline_state.active is False
        assert ps_module.pipeline_state.last_successful_run is None
        assert ps_module.pipeline_state.is_registered() is False

    def test_snapshot_none_when_not_registered(self):
        """snapshot() DEBE retornar None si el pipeline no está registrado."""
        assert ps_module.pipeline_state.snapshot() is None

    def test_mark_active_registers_pipeline(self):
        """mark_active() DEBE activar el pipeline y registrarlo."""
        ps_module.pipeline_state.mark_active()
        assert ps_module.pipeline_state.active is True
        assert ps_module.pipeline_state.is_registered() is True
        snapshot = ps_module.pipeline_state.snapshot()
        assert snapshot is not None
        assert snapshot["active"] is True
        assert snapshot["last_successful_run"] is None

    def test_mark_success_records_timestamp(self):
        """mark_success() DEBE registrar el timestamp de la última ejecución."""
        ps_module.pipeline_state.mark_success()
        assert ps_module.pipeline_state.last_successful_run is not None
        assert ps_module.pipeline_state.is_registered() is True
        snapshot = ps_module.pipeline_state.snapshot()
        assert snapshot["last_successful_run"] == (
            ps_module.pipeline_state.last_successful_run.isoformat()
        )

    def test_mark_success_with_explicit_timestamp(self):
        """mark_success(when=...) DEBE usar el timestamp provisto."""
        when = datetime(2026, 7, 31, 12, 0, 0, tzinfo=timezone.utc)
        ps_module.pipeline_state.mark_success(when=when)
        assert ps_module.pipeline_state.last_successful_run == when
        assert (
            ps_module.pipeline_state.snapshot()["last_successful_run"]
            == "2026-07-31T12:00:00+00:00"
        )

    def test_mark_success_implies_registered_without_active(self):
        """Pipeline registrado por éxito aunque no esté activo."""
        ps_module.pipeline_state.mark_success()
        assert ps_module.pipeline_state.active is False
        assert ps_module.pipeline_state.is_registered() is True
