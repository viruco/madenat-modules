# MADENAT — Estado de Continuidad Técnica

**Versión documental:** 9.2.0
**Fecha de actualización:** 2026-07-08  <!-- actualizado: 2026-07-08 — riesgo de parseo disperso en madenat_guia_processing.py agregado a sección 5 -->
**Estado:** ACTIVO — Checkpoint vivo para retoma técnica sin reconstrucción de contexto

---

## 1. Propósito

Este documento es el checkpoint técnico vivo del proyecto.
Debe permitir retomar el trabajo sin reconstruir el contexto desde cero.

---

## 2. Estado actual resumido

### Infraestructura
- Módulo: `madenat_lumber_core`.
- Target: Odoo 18 CE.
- Ambiente: Docker en WSL (`odoo18_app`, `db`).
- Arquitectura: modular parcial.

### Documentación (post-auditoría forense 2026-07-01)
- **Auditoría forense completa ejecutada** sobre TODO `custom_addons/` contra `madenat_lumber_docs/` como fuente canónica única.
- **CANON/INDICE_DOCUMENTACION.md v10.0.0:** 19 documentos CANON indexados. Versión de `02_CONTINUIDAD.md` corregida (8.1.0→9.0.0 match real).
- **WIKI/00_INDICE.md v2.0.0:** ~60 documentos WIKI indexados.
- **AD-26 ejecutado:** 33 archivos `.bak` removidos de módulos productivos → `LEGADO/backups_modulos/`.
- **Backup de módulo movido:** `madenat_lumber_core/backups/fase1_20260602_211431/` → `LEGADO/backups_modulos/`.
- **CHANGELOG cerrado:** `[Unreleased]` → `18.0.5.4.0` (fix UserError stock.moves, 2026-07-01).
- **Prueba de humo:** 86 módulos cargados en 4.71s, 0 errores, registry OK.
- **Punto de entrada:** `CANON/INDICE_DOCUMENTACION.md` → único mapa maestro.

### Verdad Funcional (Código)
1. **Naming de Largo:** Implementado vía `lengthinputraw` (preserva entrada) y `lengthuom` (unidad).
2. **Fuente de Verdad:** El campo `length` es la base normalizada en metros para todos los cálculos volumétricos.
3. **UI:** Estándar Odoo 18 verificado (uso de etiquetas `<list>` y componente `<chatter/>`).
4. **Registry:** El módulo instala y actualiza sin errores. El incidente de `@api.depends` está resuelto.
5. **Fix de Blanks (2026-06-02):** Corregido y validado en local. Ajuste volumétrico para blanks clear en `stock_lot.py` y `madenat_guia_processing.py` que evita la aplicación indebida del ajuste S2S en blanks. Ver AD-27.

---

## 3. Prioridades Actuales (2026-07-01)  <!-- actualizado: 2026-07-01 -->

1. **Completar Fase C:** Crear CHANGELOG mínimos en 7 módulos sin trazabilidad (costing, billing, shipping_core, reports, vendor_payment, toll_processing, reception_improvements).
2. **Completar Fase D:** Mover scripts de auditoría/limpieza de raíz `custom_addons/` a `LEGADO/`.
3. **Confirmar deduction_factor Blank:** 0.0625 en seed `ingestion_seed_fase3.xml` sigue vigente. Pregunta a Cristhian pendiente.
4. **Deploy a producción:** Pendiente hasta completar Fases C+D+E y validar staging.

---

## 4. Punto de retoma — 2026-07-06  <!-- actualizado: 2026-07-06 -->

**Último commit conocido:** e6a1fc1 — refactor(cleanup): consolidar reception_service hacia savepoint validado por tests A/B
**Rama:** main
**Checkpoint rollback:** d597703 (pre-consolidación, Tests A y B aprobados)
**Estado:** Fase 3 completada y validada. Consolidación de `reception_service.cleanup_orphan_moves()` hacia savepoint + force_delete aplicada. Estrategia de unlink homogeneizada entre ambos métodos sobrevivientes. Tests A y B pasando (0 failed, 0 error(s)). Auditoría documentada en `AUDITORIA_ASIMETRIA_DOCUMENTAL_20260706.md` secciones X, Y, Z, W. AD-39 actualizado con cierre funcional.
**Pendiente:** Auditoría documental canónica y revisión de deuda residual. Próximo sprint enfocado en documentación/continuidad, no en refactor funcional.
**Retomar desde e6a1fc1 con revisión documental canónica y pendientes residuales de auditoría; no reabrir refactors cerrados salvo hallazgo nuevo.**

### Cerrado en sesión 10-06-2026
- HOTFIX UX — Pestaña Comercial f5085: `thickness_visual` como columna principal, `thickness_nominal_frac` como opcional. Solo XML (lumber_reception_views.xml L372-380), 0 Python. Trazabilidad preservada vía columna opcional. Ver CHANGELOG.md.

### Cerrado en sesión 09-06-2026
- C1: Menú raíz renombrado "📥 Ingreso de Guías Dentro de Recepción" ✅
- _compute_visual_defaults para Blank (f5085): confirmado correcto, no requirió cambios ✅
- Diagnóstico completo flujos S2S vs Blank completado ✅
- SSH cuenta viruco configurado permanentemente en WSL2 ✅
- C2: Selector tipo producto operativo con labels (Madera Aserrada / Blank) ✅ — commit c6d8812 + 0cda416
- C3 (parcial): Reglas mapeo nominal 6/4, 5/4, 7/4, 8/4 en thickness_visual_ranges ✅ — commit 5732fd5
- C4: Restricción documental Packing/Guía por tipo producto ✅ — commit 0cda416
- C1 (bis): Eliminación IDs duplicados menu_remapping.xml + reorden Reportes (sequence 45) ✅ — commit 1438bb5

### Cerrado en sesión 11-06-2026
- Fix thickness_visual 6/4: max_thickness 42→46mm, 7/4 min_thickness 42→46mm ✅ — commit 3252c7e
- Migración 18.0.5.1.0 para thickness_visual 6/4 ✅ — commit 52ec1c7
- INC-010 + DEC-006 documentados ✅ — commit 7b3665f

### Cerrado en sesión 13-06-2026
- Fix R7 OC column y PDF footer colspan ✅ — commit 99545d9
- Fix R7/R8 group_by con purchase_order desde core ✅ — commit 3ba43575

### Nuevos features en staging (pendiente validación)  <!-- actualizado: 2026-06-16 -->
- Kanban, dashboards, wizard period_close, búsqueda OC — commit 8ce578b
- stock_landed_cost override y tests costing — commit 81c3373
- Restauración visibilidad PDF+Excel en todos los perfiles — commit 4372dec

### Bloqueado — esperando Cristhian  <!-- actualizado: 2026-06-16 -->
- C3: deduction_factor=0.0625 para blank_clear
  → Pregunta enviada: ¿El volumen exportación Blank usa deducción de cara 1/16" o espesor nominal exacto?
  → El valor 0.0625 sigue en `ingestion_seed_fase3.xml` sin modificar. No se toca sin confirmación.

### Pendiente activo (próxima sesión)  <!-- actualizado: 2026-06-16 -->
- Máquina remota de test: validar commit 3ba43575 en staging
- Validar nuevos features (kanban, dashboards, period_close, landed_cost) en staging
- Auditoría documental canónica completada — ver INDICE_DOCUMENTACION.md para estado

### Contexto clave descubierto
- Flujo S2S: puede modificar nominal comercial, aplica f1550, recargo +1/8"
- Flujo Blank: producto final de compra, no sufre transformación nominal,
  solo conversión de unidades (pies→m), factor f5085 (5085.312)
- _compute_visual_defaults ya separa correctamente ambos mundos (línea 481)
- deduction_factor=0.0625 en seed está documentado como "según planilla real"
  — no modificar sin confirmación de negocio

---

## 5. Riesgos activos

| Riesgo | Severidad | Estado |
|---|---|---|
| Constraint `stock_lot_check_cost_positive` | Alta | ABIERTO |
| Monolito parcial en `lumber_reception.py` (3,054 líneas, 5 responsabilidades, parseo desacoplado en reception_parser.py) | Media | ABIERTO |
| Parseo disperso en `madenat_guia_processing.py` (10 métodos sin dispatcher, 4,390 líneas, 8 responsabilidades) | Alta | ABIERTO |
| Tolerancias no formalizadas | Media | ABIERTO |
| T29–T32 sin evidencia formal | Media | PENDIENTE (no bloqueante para TEST) |

**Nota (2026-07-08):** La lógica de negocio S2S vs Blank está correctamente aislada en `_compute_vol_shipment_m3` (L476-538, bifurcación en L510-516) y NO debe tocarse ni fusionarse en ninguna intervención futura sobre el parseo disperso de `madenat_guia_processing.py`.
