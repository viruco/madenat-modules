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
