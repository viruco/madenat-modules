# MADENAT — Estado de Continuidad Técnica

**Versión documental:** 8.0.0
**Fecha de actualización:** 2026-06-02
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

## 3. Prioridades Actuales (2026-06-02)

1. **Documentar fix de blanks:** Completado en esta sesión. Ver `04_DECISION_LOG.md` entrada AD-27.
2. **Enviar a TEST:** Deploy del módulo actualizado a ambiente TEST.
3. **Validar en TEST:** Verificar funcionalidad post-fix, integridad de cálculos volumétricos para blanks y ausencia de regresiones.
4. **Decidir producción:** Si TEST pasa sin incidencias, proceder con deploy a producción.

---

## 4. Punto de retoma — 2026-06-09

**Último commit:** 2e0c7ca — fix(menu): renombrar menú raíz C1 Cristhian
**Rama:** main
**Estado:** En curso — implementando observaciones Cristhian (08-06-2026)

### Cerrado en sesión 09-06-2026
- C1: Menú raíz renombrado "📥 Ingreso de Guías Dentro de Recepción" ✅
- _compute_visual_defaults para Blank (f5085): confirmado correcto, no requirió cambios ✅
- Diagnóstico completo flujos S2S vs Blank completado ✅
- SSH cuenta viruco configurado permanentemente en WSL2 ✅

### Bloqueado — esperando Cristhian
- C3: deduction_factor=0.0625 para blank_clear
  → Pregunta enviada: ¿El volumen exportación Blank usa deducción de cara 1/16" o espesor nominal exacto?

### Pendiente activo (próxima sesión)
- C2: Mostrar tipo de producto con labels operativos en Recepción (Madera Aserrada / Blank)
- C3: Validar volúmenes Blank post-confirmación deduction_factor
- C4: Restricción documental Packing/Guía por tipo producto — requiere regla de Cristhian
- Máquina remota de test: validar commit 2e0c7ca en staging

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