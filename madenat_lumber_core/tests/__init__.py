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
# 🏷️ F3.1 — Alta automática de etiquetas SV desde guías de volumen validadas.
from . import test_f31_volume_sv_autocreate

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
# 🔧 P0-R — remediación local de la fundación Core/SV (F-01/F-02/F-04).
from . import test_p0r_acl
from . import test_p0r_sv_return
from . import test_p0r_upgrade
# 🔩 P0-R (F-P0R-A) — contrato estático manifest↔XML (dependencias externas).
from . import test_p0r_manifest_external_xml_dependencies
# 🧱 P0-R (F-P0R-B/F-P0R-C) — fixtures SV y lectura del CSV de ACL.
from . import test_p0r_fixtures
