# MADENAT — Roadmap General

**Versión:** 5.0.0  
**Fecha:** 2026-05-03  
**Última actualización:** 2026-05-03 (18:45 UTC)  
**Estado:** ACTIVO - Iniciando Fase 6 (Integración Ecosistema)

---

## 🎯 Visión General
Sistema integral de recepción y procesamiento de madera bruta para MADENAT, basado en una arquitectura modular desacoplada que garantiza trazabilidad, precisión volumétrica bajo la "Regla de Oro" y blindaje mediante Gates criptográficos.

---

## ✅ Fases Completadas

* **Fase 0.5 — Saneamiento Crítico:** Eliminación de duplicados, consolidación de lógica de anchos y validaciones de rango (1-500mm).
* **Fase 1 — Gates y Blindaje:** Implementación de Gates 0-3 con firma digital SHA-256. writes restringidos a Gate 3.
* **Fase 2 — Multi-formato y Triple Capa:** Soporte para Standard/Blanks con capas Visual, Física y Nominal operativas.
* **Fase 3 — Flujo Integral del Packing:** Validación end-to-end del flujo documental → comercial → bodega.
* **Fase 4 — Refactor Técnico (Hito Mayor):** Desacoplamiento parcial exitoso de lógica hacia servicios especializados.
    * `reception_parser.py` (Dispatcher de archivos).
    * `reception_workflow.py` (Máquina de estados y pipeline).
    * `reception_service.py` (Motor de Stock Engine).
    * `mixin_lumber_ingest.py` (Shared Kernel de validaciones).

---

## 🟠 Fase Actual

### Fase 5 — Tests y Calidad
* **Estado:** Matriz de 14 tests core ejecutada al PASS.
* **Pendiente:** Formalizar tolerancias por tipo de recepción y validar convivencia Standard + Blanks en escenarios de alto volumen (>1000 líneas).

### Fase 6 — Integración del Ecosistema (Prioridad Alta)
* **Acción Inmediata:** Creación del modelo `lumber.billing.consolidation.line`.
* **Objetivo:** Conexión del flujo de inventario con el módulo de facturación y finanzas.
* **Habilitación:** Costeo real vs estimado y cierre de brechas en tests T08/T12.

---

## ⬜ Próximas Fases

* **Fase 7 — Protocolo IA y Mantenimiento:** Aplicación del protocolo de trabajo para nuevas extensiones y limpieza de deuda técnica visual (warnings XML detectados en logs).
* **Fase 8 — Business Intelligence:** Reportes avanzados por voyage, nave y shipment. Dashboard de discrepancias comerciales.

---

## 📈 Métricas de Éxito Actuales

* **Integridad:** recepciones confirmadas vía Gate 3.
* **Trazabilidad:** lotes vinculados mediante `package_no`.
* **Calidad:** 14 tests core en verde.
* **Arquitectura:** Patrón modular aplicado parcialmente, con servicios extraídos pero archivos grandes persistentes (deuda remanente no bloqueante).

---

## ⚠️ Riesgos Activos y Mitigación

| Riesgo | Severidad | Estado Actual | Acción Requerida |
| :--- | :--- | :--- | :--- |
| **Inconsistencia Financiera** | 🔴 Alta | ⚠️ Activo | Crear modelo de consolidación de facturas (Fase 6). |
| **Tolerancias Matemáticas** | 🟡 Media | 🟠 En curso | Definir umbral de bloqueo vs advertencia en Gate 2. |
| **Warnings de UI** | 🟢 Baja | 🟠 En curso | Limpiar atributos `title` en iconos FA de las vistas XML. |
| **Monolito Técnico** | 🔴 Alta | ✅ Mitigado parcialmente | Refactor modular iniciado exitosamente en Fase 4. |

---

**Siguiente Milestone:** Integración financiera exitosa y validación completa de los tests de facturación (T08/T12).