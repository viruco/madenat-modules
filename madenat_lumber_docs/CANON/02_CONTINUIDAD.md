# MADENAT — Estado de Continuidad Técnica

**Versión documental:** 8.1.0
**Fecha de actualización:** 2026-06-16  <!-- actualizado: 2026-06-16 -->
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

### Verdad Funcional (Código)
1. **Naming de Largo:** Implementado vía `lengthinputraw` (preserva entrada) y `lengthuom` (unidad).
2. **Fuente de Verdad:** El campo `length` es la base normalizada en metros para todos los cálculos volumétricos.
3. **UI:** Estándar Odoo 18 verificado (uso de etiquetas `<list>` y componente `<chatter/>`).
4. **Registry:** El módulo instala y actualiza sin errores. El incidente de `@api.depends` está resuelto.
5. **Fix de Blanks (2026-06-02):** Corregido y validado en local. Ajuste volumétrico para blanks clear en `stock_lot.py` y `madenat_guia_processing.py` que evita la aplicación indebida del ajuste S2S en blanks. Ver AD-27.

---

## 3. Prioridades Actuales (2026-06-16)  <!-- actualizado: 2026-06-16 -->

1. **Validar en staging:** commit `3ba43575` (R7/R8 group_by + OC column + PDF footer) pendiente de verificación en máquina remota de test.
2. **Confirmar deduction_factor Blank:** 0.0625 en seed `ingestion_seed_fase3.xml` sigue vigente. Pregunta a Cristhian pendiente: ¿El volumen exportación Blank usa deducción de cara 1/16" o espesor nominal exacto?
3. **Auditoría documental canónica:** Sesión activa 2026-06-16 — revisión completa de CANON/.
4. **Deploy a producción:** Pendiente hasta que staging esté validado y auditoría documental cerrada.

---

## 4. Punto de retoma — 2026-06-16  <!-- actualizado: 2026-06-16 -->

**Último commit:** 3ba43575 — fix: align R7/R8 group_by with purchase_order from core
**Rama:** main
**Estado:** Post C1-C4. Hotfix UX cerrado. Nuevos features (kanban, dashboards, wizard period_close, landed_cost) en staging. Auditoría documental canónica en curso.

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
| Monolito parcial en `lumber_reception.py` | Media | ABIERTO |
| Tolerancias no formalizadas | Media | ABIERTO |
| T29–T32 sin evidencia formal | Media | PENDIENTE (no bloqueante para TEST) |