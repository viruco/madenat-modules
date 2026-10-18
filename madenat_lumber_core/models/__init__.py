# -*- coding: utf-8 -*-

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✅ ORDEN CRÍTICO DE CARGA DE MODELOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from . import utils_uom
from . import width_mapping
from . import excel_table_detection
from . import reception_parser
from . import validation_checklist_mixin
from . import mixin_lumber_ingest
from . import madenat_guia_processing
from . import madenat_guia_processing_historical
from . import madenat_guia_processing_documental
from . import ingestion_gate
from . import lumber_reception
from . import madenat_subproducto
from . import res_partner
from . import res_config_settings
# Fase 2 — Modelos persistentes de configuración de ingesta
from . import lumber_blank_nominal_map
from . import lumber_width_s2s_map
from . import lumber_thickness_visual_rule
from . import lumber_profile_subproduct_rule
from . import madenat_lumber_product_default
from . import madenat_ingestion_config
from . import lumber_thickness_real_map
# Fase 3 — Modelos de fórmulas de exportación (H8) y formatos de ingesta (H9)
from . import lumber_export_formula
from . import lumber_ingestion_format
from . import madenat_audit_log
from . import stock_lot
from . import stock_lot_cost_line
from . import stock_picking
from . import stock_move
from . import product_product
from . import reception_service
from . import madenat_guia_processing_source_lot_line
# 🏷️ Programa SV — infraestructura técnica interna (capacidad/marcador) y
# ledger append-only de etiquetas SV (Volumen).
from . import madenat_sv_internal
from . import madenat_sv_operation

# AD-88 (2026-10-01): mixin transversal «advertir, motivar, auditar».
from . import madenat_deviation

# Bloque 4C (AD-116 / F7): Marcador de patio en ubicaciones de inventario
from . import stock_location

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔥 VALIDACIONES AUTOMÁTICAS DE STARTUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import logging
_logger = logging.getLogger(__name__)

if not utils_uom.validate_mbf_factor():
    _logger.critical("❌ FACTOR MBF INVÁLIDO - REVISAR utils_uom.py")

if not utils_uom.validate_imperial_factor():
    _logger.critical("❌ FACTOR IMPERIAL INVÁLIDO - REVISAR utils_uom.py")

_logger.info("✅ Todas las validaciones UoM ejecutadas correctamente en startup")
