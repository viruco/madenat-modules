from . import test_lumber_reception
from . import test_length_uom_and_subproducto
from . import test_guia_processing
from . import test_duplicate_validation
from . import test_supplier_resolution
from . import test_guia_processing_display_name
from . import test_product_default
from . import test_subproducto_contract
from . import test_reception_supplier_rut_extraction
from . import test_volumen_restante
from . import test_granel_route
from . import test_parse_excel_core
from . import test_excel_table_detection
from . import test_volume_guide_header

# 🏷️ Programa SV — gestión operativa de etiquetas SV.
from . import test_sv_operation_ledger
from . import test_sv_rename
from . import test_sv_volume_regularization
from . import test_sv_rebaja
from . import test_sv_reversal_lot_specific
from . import test_sv_escalation_security
# 🔐 Endurecimiento Fase 2.1: anti-bypass y concurrencia real.
from . import test_sv_rpc_bypass
from . import test_sv_concurrency
# 🏷️ Fase 2 (AD-80): reversa SV visible en la UI (ledger + formulario Guía).
from . import test_sv_reverse_ui
# 🧪 Modo A autoservicio sin `--test-enable` (vía ir.config_parameter).
from . import test_sv_dev_cleanup_param
# AD-88 (2026-10-01): mixin transversal «advertir, motivar, auditar».
from . import test_deviation_guard
# Fase 1: semilla configurable de keywords de tipo de ingreso (paridad fallback).
from . import test_ingestion_keywords_seed
# Reset de recepción no bloqueante y trazable (reversión por movimientos).
from . import test_reception_reset_traceable
# Reapertura no bloqueante y trazable de guía procesada (Incremento G1).
from . import test_guia_reopen_traceable
# G2: vínculo persistente guía de procesado ↔ picking de ingreso de producción.
from . import test_guia_picking_link
# G3: reversión física automática del ingreso de producción (llave fuerte G2).
from . import test_guia_production_reverse
# H1: reversión física ASISTIDA de producción histórica (sin llave fuerte G2).
from . import test_guia_historical_reverse
# B1: guard server-side contra revalidación física duplicada.
from . import test_guia_revalidation_guard
# CDP-V1: corrección documental preservada (solo documental).
from . import test_guia_documental_correction
# 🔐 Fase C.1 (2026-10-04) — Seguridad de Ingreso/Recepción/Guías.
# Cierra la puerta lateral RPC/ORM (UAT-INT-4): solo Operaciones/Jefatura/
# Gerencia pueden crear/procesar/validar/reabrir/cancelar guías y recepciones.
from . import test_guia_processing_security
from . import test_reception_security
from . import test_manifest_external_xml_dependencies
# 🛡️ 2026-10-07: validación efectiva de guías duplicadas en la ingesta
# (Procesado / Volúmenes / formulario directo) reutilizando C1.
# 🛡️ 2026-10-07 (cierre): aviso no bloqueante en Recepción, prevención de
# avisos repetidos y compatibilidad de los llamadores de C1.
from . import test_guide_duplicate_warnings
from . import test_guide_duplicate_ingest
# 🛡️ 2026-10-07 — REGRESIÓN incidente guía 15183 (cross-model mismo emisor).
from . import test_guide_dup_regression_15183
# 🛡️ 2026-10-12 — DIAGNÓSTICO `stock_quant_lot_id_fkey`: la etiqueta SV con
# existencias no se elimina (guarda proactiva + traducción del error de FK).
from . import test_sv_lot_unlink_guard
# 🔐 FASE 4 (H3 / H-SEC-5) — inmutabilidad mínima de la bitácora append-only.
from . import test_audit_log_immutability
# 📐 FASE 12 (WP-B): Ancho de Exportación S2S Canónico y Opción Manual.
from . import test_export_width_s2s_wpb
# ⚖️ FASE 12 (WP-A): Regla de Equivalencia Guía vs Packing ('ok_rounded').
from . import test_guia_packing_equivalence_wpa
# 🏗️ FASE 12 (Bloque 4C / F7 / AD-116): Gestión y Filtros de Patios en Recepción.
from . import test_patios_f7
# 🌡️ FASE 12 (Bloque 4D-1 / F6 / AD-116): Secado en Horno en stock.lot.
from . import test_drying_lot_f6
# 🪵 FASE 12 (Bloque 4G/4H / G8 / AD-121): Tabla S2S — coherencia exacta decimal/etiqueta y trazabilidad chatter.
from . import test_lumber_width_s2s_map_g8
# 🛡️ FASE 12 (Bloque 4I / I3 / AD-121): Comprobación pre-deploy y normalización de versiones.
from . import test_pre_deploy_health_check
# 🎯 FASE 12 (Bloque 4J / J2 / AD-122): Prevención de doble redondeo de volúmenes y MBF.
from . import test_double_rounding_j2
# 📐 FASE 12 (Bloque 4L / L3 / AD-124): Resolución visual de anchos basada en datos.
from . import test_visual_dimension_l3
# 📏 FASE 12 (Bloque 5A / AD-126): Tabla de Espesores Reales Físicos.
from . import test_lumber_thickness_real_map_5a
# 🌲 FASE 12 (Bloque 5B / AD-126): Volumen Real Físico F3.
from . import test_vol_physical_real_5b

