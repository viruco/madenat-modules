# MADENAT — Hoja de Ruta / Backlog Canónico

**Versión:** 5.0.0  
**Fecha:** 2026-05-03  
**Última actualización:** 16:30 UTC  
**Estado:** ACTIVO - Iniciando Fase 6 (Integración Financiera)

---

## FASE 0.5 — SANEAMIENTO CRÍTICO ✅ 100% CERRADA
- [x] Eliminación de campos duplicados en `lumber_reception.py` (7 campos).
- [x] Consolidación de decoradores `@api.depends` duplicados.
- [x] Reparación de importaciones rotas (uso de `openpyxl` nativo).
- [x] Corrección de variables indefinidas (`sheet` en `action_verify_data`).
- [x] Completación de métodos base (`create`, `write`, `_onchange`).
- [x] Creación de tabla centralizada `WidthMappingTable`.
- [x] Refactorización de creación de lotes al servicio `LumberReceptionService`.
- [x] Implementación de validaciones de rango (1-500mm).
- [x] Cobertura de tests unitarios T01-T14 (Todos en verde).

---

## FASE 1 — GATES Y BLINDAJE ✅ CERRADA
- [x] Gate 0: Validación de archivos (Formatos/Tamaño).
- [x] Gate 1: Reconciliación documental (Excel vs PDF vs OC).
- [x] Gate 2: Validación de integridad comercial (Nominales/Productos).
- [x] Gate 3: Snapshot inmutable y firma SHA-256 integrada.
- [x] Bloqueo total de escrituras fuera de Gate 3.

---

## FASE 2 — MULTI-FORMATO Y TRIPLE CAPA ✅ CERRADA
- [x] Dispatcher Standard / Blanks operativo.
- [x] Triple capa (Visual / Física / Nominal) funcional en UI.
- [x] UI "Espejo Documental" validada.
- [x] Asignación automática de regla de exportación.

---

## FASE 3 — FLUJO INTEGRAL DEL PACKING ✅ CERRADA
- [x] Documentación de flujo end-to-end (Documentos -> Staging -> Bodega).
- [x] Conciliación matemática de volúmenes (`vol_physical`, `vol_purchase`, `vol_shipment`).
- [x] Propagación garantizada de `package_no` a `lot_name`.
- [x] Validación de picking generado sin contaminación de datos.

---

## FASE 4 — REFACTOR TÉCNICO (MODULARIZACIÓN) ✅ CERRADA
- [x] **Parser Dispatcher:** Extraído a `reception_parser.py`.
- [x] **Workflow Engine:** Aislado en `reception_workflow.py`.
- [x] **Stock Engine:** Lógica de inventario en `reception_service.py`.
- [x] **Shared Kernel:** Mixins de validación en `mixin_lumber_utils.py`.

---

## FASE 5 — TESTS Y CALIDAD 🟠 EN CIERRE
- [x] Matriz de 14 tests core validada al 100%.
- [ ] Definir tolerancias oficiales por tipo de madera (% desviación aceptable).
- [ ] Validar convivencia Standard + Blanks en guías masivas (>1000 líneas).
- [ ] Limpiar warnings de iconos XML (Atributos `title` en vistas).

---

## FASE 6 — ECOSISTEMA Y CONTINUIDAD 🚀 PRÓXIMO HITO
- [ ] **Facturación:** Creación del modelo `lumber.billing.consolidation.line`.
- [ ] **Integración Financiera:** Vincular recepción con líneas de factura y pagos.
- [ ] **Costeo Avanzado:** Prorrateo de costos multi-nivel.
- [ ] **Reporting:** Informes por Voyage, Nave y Shipment.

---

## FASE 7 — PROTOCOLO DE TRABAJO CON IA ✅ CERRADA / 🟠 EN USO
- [x] Definir cápsula de contexto y flujo de feedback.
- [x] Reglas de actualización por archivo (Shared Kernel vs Contexto).
- [ ] Aplicación sistemática del protocolo en el desarrollo de la Fase 6.

---

## FASE 7.1 — DESCOMPOSICIÓN DE MÓDULOS GIGANTES ⬜ PENDIENTE
**Prioridad:** BAJA (Refactor de mejora, no bloqueante)  
**Estimado:** 2-3 horas  
**Razón:** `lumber_reception.py` tiene 3500+ líneas (LumberReceptionLine + LumberReception integradas)

- [ ] Separar `LumberReceptionLine` en archivo propio: `lumber_reception_line.py`
- [ ] Actualizar imports en `__init__.py`
- [ ] Validar que todos los tests sigan pasando
- [ ] Documentar estructura modular en `00_ARQUITECTURA.md`

**Notas:**
- Actualmente funciona perfectamente integrado
- Separación mejorará mantenibilidad pero NO añade funcionalidad
- Debe hacerse DESPUÉS de Fase 6 (para no interrumpir integración financiera)

---

## ⚠️ RIESGOS ACTIVOS

| Riesgo | Severidad | Acción | Estado |
| :--- | :--- | :--- | :--- |
| **Facturación Ausente** | Alta | Crear `lumber.billing...` | ⚠️ Crítico (Fase 6) |
| **Tolerancias No Formalizadas** | Media | Definir umbrales en Fase 5 | 🟠 En curso |
| **Orquestador Monolítico** | Alta | Refactor Modular | ✅ Mitigado |
| **`package_no` no propagado** | Alta | Validación Test T11 | ✅ Mitigado |

---

## 🏁 DEFINICIÓN DE TERMINADO (HITOS 5 Y 6)

Se considerarán cerradas cuando:
1. Los 14 tests pasen integrando el modelo de facturación (`lumber.billing.consolidation.line`).
2. Las tolerancias matemáticas de volumen y costo estén parametrizadas y probadas.
3. La interfaz esté libre de warnings XML en los logs.
4. El flujo completo genere el asiento contable de una guía real (ej. 40597) de forma automática.