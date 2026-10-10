# -*- coding: utf-8 -*-
from . import test_sv_allocation
from . import test_shipment_view_module_independence
from . import test_container_lot_wizard_disponible
from . import test_consolidation_action_domain
from . import test_rebaja_contenedor
# I1 canónico (CANON/19 §16, 2026-10-02): ubicaciones y saldo por procesador.
from . import test_processor_locations
# AD-89/AD-90 (2026-10-02): envío parcial, reservas y backorder.
from . import test_processor_shipment_ad89
# I2 (CANON/19 v1.6.0 / AD-91): imputación documental SV.
from . import test_sv_imputation_i2
# I2 candidatos SV contextuales (contrato canónico único, AD-91).
from . import test_sv_imputation_candidates
# AD-92 (2026-10-05): rolleo centrado en Embarque.
from . import test_vessel_rollover
# Sub-bloque 2 (2026-10-04): retorno seguro a borrador de Embarque (AD-93).
from . import test_shipment_return_to_draft
# Sub-bloque 3 (2026-10-04): zarpe con excepción documental B-01 (Política B).
from . import test_shipment_b01_exception
# Sub-bloque 4A (2026-10-04): regularización B-01 R1 y cierre controlado R4.
from . import test_b01_regularization
# Sub-bloque 4B (2026-10-04): R2 retorno físico total / reversa robusta de rebaja.
from . import test_rebaja_return_total
# Sub-bloque 5 (2026-10-04): Entrega/Cierre seguro (Política D2).
from . import test_shipment_delivery_safe
# Corrección B2 (2026-10-05): fuente única de estado documental.
from . import test_document_status_b2
# Corrección 2026-10-04: backlog documental NO bloqueante.
from . import test_documentary_backlog
# Identificación de retorno de servicio: filtro y reglas I2 (2026-10-07).
from . import test_service_return_pending_filter
from . import test_service_return_imputation_guard
