# -*- coding: utf-8 -*-
# =============================================================================
# MÓDULO:   madenat_lumber_core.tests.test_ingestion_gate
# ARCHIVO:  tests/test_ingestion_gate.py
# DESCRIPCIÓN: Tests unitarios para Gate 0 y Gate 1.
#              Ejecutar con: pytest tests/test_ingestion_gate.py -v
#
# FASE:     1 — Gates de Validación
# VERSIÓN:  1.0.0
# FECHA:    2026-04-03
# =============================================================================

import pytest
from unittest.mock import MagicMock, patch
from models.ingestion_gate import (
    Gate0PreUpload,
    Gate1DocumentReconciliation,
    ValidationResult,
)


# =============================================================================
# FIXTURES COMUNES
# =============================================================================

@pytest.fixture
def mock_env():
    """Odoo environment simulado para tests sin BD."""
    env = MagicMock()
    # Simular que la guía NO existe (caso nominal)
    env["madenat.guia.processing"].search.return_value = MagicMock(
        __bool__=lambda self: False
    )
    # Simular tipo_cambio_referencia configurado
    env["ir.config_parameter"].sudo().get_param.return_value = "950.00"
    return env


@pytest.fixture
def excel_ok():
    return {"nro_guia": "19846", "total_vol_m3": 48.50, "tipo_cambio": 940.0}


@pytest.fixture
def pdf_ok():
    return {"nro_guia": "19846", "total_vol_m3": 48.80}


# =============================================================================
# GATE 0 — PRE-UPLOAD
# =============================================================================

class TestGate0PreUpload:

    def setup_method(self):
        self.gate = Gate0PreUpload()
        self.valid_excel = b"PK\x03\x04" + b"0" * 100  # xlsx magic bytes simulados

    def test_excel_valido(self):
        result = self.gate.validate("guia_19846.xlsx", self.valid_excel, "excel")
        assert result.is_valid
        assert len(result.errors) == 0

    def test_pdf_valido(self):
        pdf_bytes = b"%PDF-1.4" + b"0" * 100
        result = self.gate.validate("GDE-19846.pdf", pdf_bytes, "pdf")
        assert result.is_valid

    def test_extension_incorrecta_excel(self):
        result = self.gate.validate("guia.pdf", self.valid_excel, "excel")
        assert not result.is_valid
        assert any(e.code == "FILE_EXTENSION_INVALID" for e in result.errors)

    def test_extension_incorrecta_pdf(self):
        result = self.gate.validate("guia.xlsx", b"data", "pdf")
        assert not result.is_valid
        assert any(e.code == "FILE_EXTENSION_INVALID" for e in result.errors)

    def test_archivo_vacio(self):
        result = self.gate.validate("guia.xlsx", b"", "excel")
        assert not result.is_valid
        assert any(e.code == "FILE_EMPTY" for e in result.errors)

    def test_archivo_muy_grande(self):
        big_file = b"0" * (21 * 1024 * 1024)  # 21 MB > límite de 20 MB
        result = self.gate.validate("guia.xlsx", big_file, "excel")
        assert not result.is_valid
        assert any(e.code == "FILE_TOO_LARGE" for e in result.errors)


# =============================================================================
# GATE 1 — RECONCILIACIÓN DOCUMENTAL
# =============================================================================

class TestGate1DocumentReconciliation:

    def setup_method(self, mock_env):
        pass  # env se inyecta por fixture en cada test

    def test_reconciliacion_ok(self, mock_env, excel_ok, pdf_ok):
        gate = Gate1DocumentReconciliation(mock_env)
        result = gate.validate(excel_ok, pdf_ok)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_nroguia_mismatch(self, mock_env, excel_ok, pdf_ok):
        pdf_ok["nro_guia"] = "19847"  # ← diferente al Excel
        gate = Gate1DocumentReconciliation(mock_env)
        result = gate.validate(excel_ok, pdf_ok)
        assert not result.is_valid
        assert any(e.code == "NROGUIA_MISMATCH" for e in result.errors)

    def test_nroguia_duplicado_en_bd(self, mock_env, excel_ok, pdf_ok):
        # Simular que la guía YA existe en BD
        mock_guia = MagicMock()
        mock_guia.__bool__ = lambda self: True
        mock_guia.id = 42
        mock_guia.state = "done"
        mock_env["madenat.guia.processing"].search.return_value = mock_guia

        gate = Gate1DocumentReconciliation(mock_env)
        result = gate.validate(excel_ok, pdf_ok)
        assert not result.is_valid
        assert any(e.code == "NROGUIA_DUPLICATE" for e in result.errors)

    def test_tipo_cambio_cero(self, mock_env, excel_ok, pdf_ok):
        excel_ok["tipo_cambio"] = 0
        gate = Gate1DocumentReconciliation(mock_env)
        result = gate.validate(excel_ok, pdf_ok)
        assert not result.is_valid
        assert any(e.code == "TIPO_CAMBIO_ZERO" for e in result.errors)

    def test_tipo_cambio_fuera_de_rango_genera_warning(self, mock_env, excel_ok, pdf_ok):
        excel_ok["tipo_cambio"] = 100.0  # Muy lejos de 950 referencia
        gate = Gate1DocumentReconciliation(mock_env)
        result = gate.validate(excel_ok, pdf_ok)
        assert result.is_valid  # No es error bloqueante
        assert result.has_warnings
        assert any(w.code == "TIPO_CAMBIO_OUT_OF_RANGE" for w in result.warnings)

    def test_volumen_mismatch_bloquea(self, mock_env, excel_ok, pdf_ok):
        pdf_ok["total_vol_m3"] = 60.0   # 23% de diferencia vs 48.5 → supera 2%
        gate = Gate1DocumentReconciliation(mock_env)
        result = gate.validate(excel_ok, pdf_ok)
        assert not result.is_valid
        assert any(e.code == "VOLUMEN_MISMATCH" for e in result.errors)

    def test_volumen_dentro_tolerancia(self, mock_env, excel_ok, pdf_ok):
        pdf_ok["total_vol_m3"] = 48.60  # 0.2% diferencia → dentro del 2%
        gate = Gate1DocumentReconciliation(mock_env)
        result = gate.validate(excel_ok, pdf_ok)
        assert result.is_valid

    def test_oc_no_existe(self, mock_env, excel_ok, pdf_ok):
        mock_env["purchase.order"].browse.return_value.exists.return_value = False
        gate = Gate1DocumentReconciliation(mock_env)
        result = gate.validate(excel_ok, pdf_ok, oc_id=999)
        assert not result.is_valid
        assert any(e.code == "OC_NOT_FOUND" for e in result.errors)

    def test_oc_cancelada_bloquea(self, mock_env, excel_ok, pdf_ok):
        mock_oc = MagicMock()
        mock_oc.exists.return_value = True
        mock_oc.state = "cancel"
        mock_oc.name = "OC/2026/0001"
        mock_env["purchase.order"].browse.return_value = mock_oc
        gate = Gate1DocumentReconciliation(mock_env)
        result = gate.validate(excel_ok, pdf_ok, oc_id=1)
        assert not result.is_valid
        assert any(e.code == "OC_INVALID_STATE" for e in result.errors)

    def test_sin_oc_no_verifica_oc(self, mock_env, excel_ok, pdf_ok):
        gate = Gate1DocumentReconciliation(mock_env)
        result = gate.validate(excel_ok, pdf_ok, oc_id=None)
        assert result.is_valid
        mock_env["purchase.order"].browse.assert_not_called()
