# Hoja de Ruta Ejecutiva — MADENAT Lumber Core

**Estado:** ACTIVO  
**Última actualización:** 2026-10-17  
**Fase activa:** FASE 12 — Requerimientos de Operaciones (Cristhian)  
**Objetivo:** Guiar el avance técnico y ejecutivo del sistema MADENAT (Odoo 18 CE) manteniendo alineación estricta entre decisiones de negocio (Mauricio), requerimientos operativos (Cristhian) y el código en producción.

---

## 1. Estado General y Arquitectura

El sistema opera sobre una base arquitectónica robusta y documentada:
- **Puerta de Entrada Unificada (`madenat_lumber_intake`):** Consola única para recepciones de madera bruta (compra directa) y guías de procesamiento (maquila / servicios), con navegación especializada para «Ingresos por Volúmenes» (AD-111).
- **Motor de Ingesta Normalizada (`madenat_ingestion_engine`):** Extracción agnóstica de documentos (Excel/PDF) con soporte de perfiles métricos/imperiales y plantilla estándar descargable para aserraderos sin integración automática (AD-112).
- **Consolidación y Exportación (`madenat_lumber_logistics`):** Trazabilidad documental de rebajas SV, blindaje contra sobreconsumos de etiquetas (techo duro) y unificación de rótulos de volumen («Vol. Compra (m³)», «Vol. Export (m³)», «Vol. Documental (m³)»).

---

## 2. Hitos y Fases Recientes

| Fase / Hito | Decisión Canon | Estado | Alcance Principal |
| :--- | :---: | :---: | :--- |
| **FASE 10** | AD-109 | **Local OK** (Pend. Verif. / TEST) | Registro de etiquetas en rebaja SV: clave documental única (S1), filtro de borrador en preparación (S2), y bloqueo de guardado sin selección (S3). Implementada y probada en local; pendiente verificación manual Mauricio y despliegue a TEST. |
| **FASE 11** | AD-110 | **Local OK** (Pend. Verif. / TEST) | Integridad del ciclo de vida de imputaciones SV: blindaje contra mutación de `state` fuera de acciones oficiales (A-1/B-1), reversa protegida con locks de recursos (M-2), trazabilidad encadenada origin↔reversed (M-4) y anulación con motivo firmado (B-3). Implementada y probada en local; pendiente verificación manual Mauricio y despliegue a TEST. |
| **FASE 12 (Bloque 1)** | AD-111 | **Local OK** | Operaciones Bloque 1: Menú y búsqueda por estado en «Ingresos por Volúmenes» (WP-C), unificación canónica de rótulos de volumen en embarque y contenedores (WP-B), e investigación causa raíz guía 95806 / JCE (D-E0-3). |
| **FASE 12 (Bloque 2)** | AD-112 | **Local OK** | Operaciones Bloque 2: Disponibilidad de etiquetas en imputación SV (WP-F P1–P5), plantilla estándar métrica descargable y guía de llenado (WP-E), y alineación documental wiki/canon (WP-G). |
| **FASE 12 (Bloque 3)** | — | **Detenido** (Pendiente Autorización) | Alcance aprobado: WP-B ancho de exportación (tabla existente en `width_mapping.py` y `lumber.width.s2s.map`, simulación de solo lectura sobre embarques existentes, sin recalcular valores almacenados, opción manual con usuario y fecha) y WP-A comparación guía vs packing (a la precisión declarada de la guía con tope de 3 decimales, estado `ok_rounded`, parametrizable). WP-D (patios) sigue EN ESPERA (no existe "conciliación documental" ni "imputación diferida" aprobadas). |

---

## 3. Prioridades Ejecutivas y Próximos Pasos

1. **Revisión de Checkpoint Bloque 2:** Validación funcional en navegador por parte de Mauricio de los cambios de WP-F (toggle deshabilitado para etiquetas sin saldo, pestaña «Sin disponibilidad», resumen y mensaje de error nominativo) y de WP-E (plantilla Excel generada).
2. **Definición de Bloque 3:** Autorización explícita de Mauricio respecto al inicio de WP-B ancho de exportación y WP-A comparación guía vs packing (manteniendo WP-D patios en espera).
3. **Decisiones de Negocio Pendientes (Sin alteración de código previa):**
   - **Guía 95806 (JCE):** Decidir entre renombramiento del partner 2417 o reclasificación de la guía de despacho.
   - **Documento Histórico `IMP02220`:** Decidir anulación o preservación en UI del documento aplicado con 0 repartos.
   - **Documento Histórico `IMP04823`:** Conservar como evidencia histórica anulada o recrear rebaja limpia de guía 1198.

---

## 4. Riesgos Activos y Criterios de Blindaje

| Riesgo | Severidad | Mitigación Implementada |
| :--- | :---: | :--- |
| **Sobreconsumo de Etiquetas en Imputaciones Concurrentes** | Crítica | Locks transaccionales deterministas (`pg_try_advisory_xact_lock`), validación dura de techo nominal en `_i2_validate_hard_cap` y bloqueo visual en UI con `readonly="not asignable"`. |
| **Mutaciones No Autorizadas de Estado de Negocio** | Alta | Vía privada `_i2_write_protected_state` y rechazo estricto en `write()` público para transiciones sin acción oficial. |
| **Inconsistencia de Volúmenes por Rótulos Ambiguos** | Media | Homologación estandarizada en todas las vistas: «Vol. Compra (m³)» vs «Vol. Export (m³)» vs «Vol. Documental (m³)» (WP-B). |
| **Colisión de Puertos / Despliegue en Entorno de Pruebas** | Baja | Protocolo estricto CLI con puerto aislado 8070 y pruebas locales por nombre sin `-u all`. |