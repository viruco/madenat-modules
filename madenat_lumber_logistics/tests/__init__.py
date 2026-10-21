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
# Bloque A/B/C (CANON/19 §19.11, 2026-10-10): relación de conciliación
# envío a procesador ↔ retorno.
from . import test_processor_return_link
# Operación manual de asignaciones centrada en SV (CANON/19 §19.14, 2026-10-10).
from . import test_sv_imputation_manual
# Unificación de acceso «Rebaja de etiquetas» (NAV-01..12, 2026-10-10).
from . import test_sv_rebaja_navigation
# Operación y blindaje de «Rebaja de etiquetas» (RET/UX/VOL/SEC/REV/PHY/CON).
from . import test_sv_rebaja_operativa
# Selección y asignación explícita al SV de trabajo (ERR/ASG/VOL/PER/SEC/PHY).
from . import test_sv_rebaja_seleccion_asignacion
# Material del packing list en el asistente (MAP/GRAN/SEM/AMT/ARCH).
from . import test_sv_rebaja_material
# Interfaz clara y concisa de ambas pestañas (CAB/EDIT/MED/ETQ/SIN/USE/MULTI/ARCH).
from . import test_sv_rebaja_ui_limpia
# Blindaje del ciclo documental (AUD-ETQ-01..05, 2026-10-11).
from . import test_sv_rebaja_blindaje
# Cierre probatorio (AUD-ETQ-06..10, 2026-10-11).
from . import test_sv_rebaja_cierre
# Contrato de aplicación (POL-01..08, política aprobada 2026-10-11).
from . import test_sv_rebaja_contrato
# Persistencia y recuperación del trabajo (SAVE/FLOW/PHY, 2026-10-11).
from . import test_sv_rebaja_persistencia
# Acciones visibles del asistente (UI/MAINT, 2026-10-11).
from . import test_sv_rebaja_ui_acciones
# Simplificación operativa de la rebaja (SIMPLE/CLIENT, 2026-10-11).
from . import test_sv_rebaja_simple
# Volver a borrador y reasignar (RESET, 2026-10-11).
from . import test_sv_rebaja_reset
# Concurrencia real de la reapertura (RESET-16/17, 2026-10-12).
from . import test_sv_rebaja_reset_concurrency
# P1 (AUD-ETQ-11): concurrencia sobre la capacidad de la misma etiqueta retornada.
from . import test_sv_rebaja_reset_lot_capacity
# P4 (AUD-ETQ-09): aislamiento y limpieza de la autorización de reapertura.
from . import test_sv_rebaja_reset_token
# P3 (AUD-ETQ-10): saldos almacenados canónicos vs derechos del usuario.
from . import test_sv_assignment_user_rights
# LOCK (2026-10-12): protección contra sobrescritura concurrente de borradores.
from . import test_sv_rebaja_save_lock
# V1 (2026-10-12): cobertura de cruces con EDICIÓN DIRECTA (matriz C1–C8).
from . import test_sv_rebaja_save_lock_direct
# V3 (2026-10-12): transacción, SerializationFailure y orden de bloqueos (TX).
from . import test_sv_rebaja_save_lock_tx
# HOTFIX OWL (2026-10-12): chatter canónico `<chatter/>` (VIEW-01..05).
from . import test_hotfix_owl_chatter
# S2 (FASE 10, 2026-10-15): «Trabajo en preparación» con filtro EFECTIVO por
# estado (F2) y «Continuar» operativo sobre estados terminales (WF-01..07).
from . import test_sv_rebaja_work_filter
# S3 (FASE 10, 2026-10-15): bloqueo del guardado/aplicación de un documento de
# rebaja VACÍO, sin borrado silencioso (F3; SG-01..06).
from . import test_sv_rebaja_empty_guard
# FASE 11 (2026-10-15): integridad del ciclo de vida de las imputaciones
# (A-1, B-1, M-2, M-4, B-2, B-3).
from . import test_sv_imputation_lifecycle_integrity
# FASE 12 (Bloque 1 / WP-B rótulos, 2026-10-17): unificación de rótulos de volumen.
from . import test_volume_labels_unification
# FASE 12 (Bloque 2 / WP-F P1-P5, 2026-10-17): disponibilidad de etiquetas en imputación SV.
from . import test_sv_imputation_availability_p1_p5
# 🔐 H0-A (Auditoría Higiene 2026-10-20): Permisos de modelos y asistentes sin ACL.
from . import test_h0_security_permissions
# H4 / AD-130: Propagación de ancho manual en lumber.shipment.line
from . import test_shipment_line_export_width


