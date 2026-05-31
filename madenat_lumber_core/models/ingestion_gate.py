# -*- coding: utf-8 -*-
# =============================================================================
# MÓDULO:       madenat_lumber_core.models.ingestion_gate
# ARCHIVO:      models/ingestion_gate.py
# DESCRIPCIÓN:  Gates de Validación para el Pipeline de Ingesta MADENAT.
#               Responsabilidad ÚNICA: validar. Nunca procesar ni escribir en BD.
#
# FASE:         1 — Gates de Validación
# CHECKPOINT:   FASE_1 / STEP_4 — Gate 3 (Notario Criptográfico)
# VERSIÓN:      1.2.0
# FECHA:        2026-04-05
# =============================================================================

import hashlib
import logging
import re
import json
import base64
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

_logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES DE CONFIGURACIÓN
# =============================================================================
TOLERANCIA_VOLUMEN_DEFAULT = 0.02          # 2%
TOLERANCIA_TIPO_CAMBIO_DEFAULT = 0.20      # ±20%
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024     # 20 MB
EXTENSIONES_EXCEL = {".xlsx", ".xls"}
EXTENSIONES_PDF   = {".pdf"}

# =============================================================================
# RESULTADO DE VALIDACIÓN — Estructura inmutable de retorno
# =============================================================================
@dataclass
class ValidationError:
    """Error bloqueante. Impide continuar el flujo."""
    code:    str
    message: str
    field:   Optional[str] = None

@dataclass
class ValidationWarning:
    """Advertencia no bloqueante. Requiere confirmación pero no detiene."""
    code:    str
    message: str
    field:   Optional[str] = None

@dataclass
class ValidationResult:
    """Resultado completo de un Gate de validación."""
    errors:   List[ValidationError]   = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)

    def add_error(self, code: str, message: str, field: str = None) -> "ValidationResult":
        self.errors.append(ValidationError(code=code, message=message, field=field))
        return self

    def add_warning(self, code: str, message: str, field: str = None) -> "ValidationResult":
        self.warnings.append(ValidationWarning(code=code, message=message, field=field))
        return self

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    @property
    def user_message(self) -> str:
        if self.is_valid and not self.has_warnings:
            return "✅ Validación exitosa."
        lines = []
        if self.errors:
            lines.append("⛔ No se puede continuar. Se encontraron los siguientes problemas:\n")
            for err in self.errors:
                field_hint = f" (campo: {err.field})" if err.field else ""
                lines.append(f"  • [{err.code}]{field_hint} {err.message}")
        if self.warnings:
            lines.append("\n⚠️ Advertencias (requieren confirmación):")
            for w in self.warnings:
                field_hint = f" (campo: {w.field})" if w.field else ""
                lines.append(f"  • [{w.code}]{field_hint} {w.message}")
        return "\n".join(lines)

    @property
    def audit_summary(self) -> str:
        return f"errors={len(self.errors)} warnings={len(self.warnings)} valid={self.is_valid}"

# =============================================================================
# GATE 0 — PRE-UPLOAD (VALIDACIÓN DE ARCHIVOS)
# =============================================================================
class Gate0PreUpload:
    def validate(self, filename: str, file_bytes: bytes, expected_type: str) -> ValidationResult:
        result = ValidationResult()
        extension = self._get_extension(filename)

        if expected_type == "excel" and extension not in EXTENSIONES_EXCEL:
            result.add_error("FILE_EXTENSION_INVALID", f"El archivo '{filename}' no es un Excel válido.", "excel_file")
        elif expected_type == "pdf" and extension not in EXTENSIONES_PDF:
            result.add_error("FILE_EXTENSION_INVALID", f"El archivo '{filename}' no es un PDF válido.", "pdf_file")

        if len(file_bytes) == 0:
            result.add_error("FILE_EMPTY", f"El archivo '{filename}' está vacío.", f"{expected_type}_file")
        elif len(file_bytes) > MAX_FILE_SIZE_BYTES:
            result.add_error("FILE_TOO_LARGE", f"Archivo '{filename}' supera el límite de 20MB.", f"{expected_type}_file")

        return result

    @staticmethod
    def _get_extension(filename: str) -> str:
        idx = filename.rfind(".")
        return filename[idx:].lower() if idx != -1 else ""

# =============================================================================
# GATE 1 — POST-PARSE / RECONCILIACIÓN DOCUMENTAL
# =============================================================================
class Gate1DocumentReconciliation:
    def __init__(self, env, tolerancia_volumen=TOLERANCIA_VOLUMEN_DEFAULT, tolerancia_tipo_cambio=TOLERANCIA_TIPO_CAMBIO_DEFAULT):
        self.env = env
        self.tol_vol = tolerancia_volumen
        self.tol_tc = tolerancia_tipo_cambio

    def _normalize_guide_no(self, guide_raw):
        if not guide_raw: return ""
        clean = str(guide_raw).upper().replace("\xa0", " ").strip()
        clean = re.sub(r"^(GUIA|GUÍA|NRO|N°|Nº)\s*[:\-]?\s*", "", clean)
        return clean.replace(".", "").replace(" ", "")

    def _safe_float(self, value, default=0.0):
        try:
            if not value: return default
            return float(str(value).replace(",", "."))
        except: return default

    def validate(self, excel_data: dict, pdf_data: dict, oc_id=None):
        result = ValidationResult()
        
        # 1. Match Nro Guía
        nro_excel = self._normalize_guide_no(excel_data.get("nro_guia"))
        nro_pdf = self._normalize_guide_no(pdf_data.get("nro_guia"))
        if nro_excel and nro_pdf and nro_excel != nro_pdf:
            result.add_error("NROGUIA_MISMATCH", f"Guía no coincide: Excel ({nro_excel}) != PDF ({nro_pdf})")

        # 2. Match Volumen
        vol_excel = self._safe_float(excel_data.get("total_vol_m3"))
        vol_pdf = self._safe_float(pdf_data.get("total_vol_m3"))
        if vol_excel > 0 and vol_pdf > 0:
            diff = abs(vol_excel - vol_pdf) / vol_excel
            if diff > self.tol_vol:
                result.add_error("VOLUMEN_MISMATCH", f"Diferencia volumen: {vol_excel}m3 vs {vol_pdf}m3 (>{self.tol_vol*100}%)")

        # 3. Tipo Cambio
        tc_excel = self._safe_float(excel_data.get("tipo_cambio"))
        tc_pdf = self._safe_float(pdf_data.get("tipo_cambio"))
        if tc_excel > 0 and tc_pdf > 0:
            if abs(tc_excel - tc_pdf) / tc_excel > self.tol_tc:
                result.add_warning("TIPO_CAMBIO_OUT_OF_RANGE", "El tipo de cambio difiere significativamente entre fuentes.")

        _logger.info("✅ [Gate1] Reconciliación completada: %s", result.audit_summary)
        return result

# =============================================================================
# GATE 2 — POST-ANÁLISIS COMERCIAL (VALIDACIÓN SOBRE STAGING)
# =============================================================================
class Gate2CommercialAnalysis:
    def __init__(self, env, tolerancia_volumen: float = 0.02):
        self.env = env
        self.tol_vol = tolerancia_volumen

    def validate(self, staging_lines) -> "ValidationResult":
        result = ValidationResult()
        if not staging_lines:
            result.add_error("EMPTY_STAGING", "El staging está vacío. No hay líneas para validar.")
            return result

        for line in staging_lines:
            lot_ref = line.lot_name or f"ID-{line.id}"
            if not line.thickness_nominal or line.thickness_nominal <= 0:
                result.add_error("NOMINAL_THICKNESS_INVALID", f"Lote {lot_ref}: Espesor nominal <= 0.", "thickness_nominal")
            if not line.width_nominal or line.width_nominal <= 0:
                result.add_error("NOMINAL_WIDTH_INVALID", f"Lote {lot_ref}: Ancho nominal <= 0.", "width_nominal")
            if not line.subproduct_id:
                result.add_error("SUBPRODUCT_MISSING", f"Lote {lot_ref}: Sin subproducto definido.", "subproduct_id")
            if not line.product_id:
                result.add_error("PRODUCT_NOT_FOUND", f"Lote {lot_ref}: Sin producto catálogo.", "product_id")

        _logger.info("✅ [Gate2] Análisis Comercial completado: %s", result.audit_summary)
        return result

# =============================================================================
# GATE 3 — PRE-COMMIT (NOTARIO CRIPTOGRÁFICO)
# =============================================================================
class Gate3PreCommit:
    """
    Genera un Snapshot inmutable y una firma criptográfica SHA-256.
    """
    def __init__(self, env):
        self.env = env
        self.user = env.user

    def generate_signature(self, reception, staging_lines):
        payload = {
            "reception_id": reception.id,
            "guide_no": reception.name,
            "timestamp_utc": datetime.utcnow().isoformat(),
            "operator_id": self.user.id,
            "total_commercial_m3": reception.commercial_volume_m3,
            "lines": []
        }
        for line in staging_lines:
            payload["lines"].append({
                "lot_name": line.lot_name,
                "vol_purchase_m3": line.vol_purchase_m3,
                "vol_shipment_m3": line.vol_shipment_m3,
                "pieces": line.pieces
            })

        json_snapshot = json.dumps(payload, sort_keys=True)
        sha256_hash = hashlib.sha256(json_snapshot.encode('utf-8')).hexdigest()
        return json_snapshot, sha256_hash


# =============================================================================
# PUNTO DE INTEGRACIÓN — Cómo llamar los Gates desde lumber_reception.py
# =============================================================================
#
# En lumber_reception.py → método action_process_files():
#
#   from .ingestion_gate import Gate0PreUpload, Gate1DocumentReconciliation
#
#   # --- Gate 0: validar archivos antes de parsear ---
#   gate0 = Gate0PreUpload()
#   for fname, fbytes, ftype in [(excel_name, excel_bytes, "excel"),
#                                (pdf_name,   pdf_bytes,   "pdf")]:
#       r = gate0.validate(fname, fbytes, ftype)
#       if not r.is_valid:
#           raise UserError(r.user_message)
#
#   # --- Parsear (código existente sin modificar) ---
#   excel_data = self._parse_excel(excel_bytes)
#   pdf_data   = self._parse_pdf(pdf_bytes)
#
#   # --- Gate 1: reconciliar documentos ---
#   gate1 = Gate1DocumentReconciliation(self.env)
#   result = gate1.validate(excel_data, pdf_data, oc_id=self.purchase_order_id.id)
#   if not result.is_valid:
#       raise UserError(result.user_message)
#   if result.has_warnings:
#       # Mostrar advertencias pero permitir continuar (requiere confirmación UI)
#       self.ingestion_warnings = result.user_message
#
# =============================================================================
