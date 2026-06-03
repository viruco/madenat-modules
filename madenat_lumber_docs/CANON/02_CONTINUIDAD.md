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

## 4. Punto de retoma

Al reanudar trabajo:
- Leer `05_BACKLOG.md` para la tarea activa.
- Confirmar que el fix de blanks ya está documentado (AD-27) y validado en local.
- La prioridad inmediata es el deploy a TEST, no revalidar T29–T32 ni Fase 6 UI.

### Próximos 3 pasos
1. Preparar y ejecutar deploy a TEST del módulo `madenat_lumber_core`.
2. Validar cálculos volumétricos de blanks en ambiente TEST (guía de referencia: `40597`).
3. Registrar resultado de validación y decidir si se procede a producción.

---

## 5. Riesgos activos

| Riesgo | Severidad | Estado |
|---|---|---|
| Constraint `stock_lot_check_cost_positive` | Alta | ABIERTO |
| Monolito parcial en `lumber_reception.py` | Media | ABIERTO |
| Tolerancias no formalizadas | Media | ABIERTO |
| T29–T32 sin evidencia formal | Media | PENDIENTE (no bloqueante para TEST) |