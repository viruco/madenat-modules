# MADENAT — Estado de Continuidad Técnica

**Versión documental:** 7.0.0
**Fecha de actualización:** 2026-05-28
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
---
## 3. Prioridades Actuales
1. **Validación UI Largo:** Ejecutar y registrar evidencia física de T29 (ft), T30 (mm) y T31 (m).
2. **Validación UI Fase 6:** Ejecutar flujo `action_create_consolidation_from_shipment` desde la interfaz.
3. **Quick-create:** Validar T32 para subproductos en el wizard.

---