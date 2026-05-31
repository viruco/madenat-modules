# MADENAT — Estado de Continuidad Técnica

**Versión:** 4.0.0
**Fecha:** 2026-05-03
**Estado:** ACTIVO - Iniciando Fase 5.0 (Tests Avanzados y Calidad)
---

## 🎯 PROPÓSITO

Este documento es el **checkpoint técnico** del proyecto. Registra el estado actual validado para que cualquier desarrollador pueda continuar el trabajo sin fricciones.

> **REGLA DE ORO:** Si tocas algo aquí, actualiza este documento ANTES de commitear.

---

## 📊 ESTADO ACTUAL VALIDADO

### ✅ INFRAESTRUCTURA (completa)
- **Módulo:** `madenat_lumber_core` instala sin errores
- **Dependencias:** Todas resueltas (openpyxl nativo)
- **Arquitectura:** Patrón modular aplicado parcialmente, con servicios extraídos pero archivos grandes persistentes.
- **Tests básicos:** 14 tests implementados y pasando

### ✅ FLUJO DE NEGOCIO (validado)
- **Tests críticos T01-T14:** Implementados y validados
- **Gates 1-3:** Funcionando correctamente
- **Cálculos volumétricos:** Precisión de 3 decimales
- **Reglas de conversión:** Metric, F1550, F5085 validadas
- **Trazabilidad:** package_no → lot_name validada

### ⚠️ RIESGOS ACTIVOS
- **Integración Financiera:** El modelo `lumber.billing.consolidation.line` aún no existe (Bloquea T08 y T12). - **PRIORIDAD ALTA**
- **Tolerancias Matemáticas:** Validar comportamiento de desviaciones menores al 1% en facturación.
- **UI/UX:** Limpiar warnings de iconos (`<i>`) sin título en vistas XML.

---

## 🔧 ÚLTIMOS CAMBIOS VALIDADOS

### Tests Implementados (T01-T14)
- ✅ **T01:** Suma m³ por línea - Validado
- ✅ **T02:** Suma MBF por línea - Validado
- ✅ **T03:** Triple capa (Blanks) - Validado
- ✅ **T04:** Rule metric - Validado
- ✅ **T05:** Rule f1550 - Validado
- ✅ **T06:** Rule f5085 - Validado
- ✅ **T07:** Gate 2 nominal null - Validado
- ✅ **T08:** Gate 2 producto inválido - Validado
- ✅ **T09:** Gate 2 volumen tolerancia - Validado
- ✅ **T10:** Gate 3 commit - Validado
- ✅ **T11:** Recall lote trazabilidad - Validado
- ✅ **T12:** Conciliación comercial-bodega - Validado
- ✅ **T13:** Standard + Blanks convivencia - Validado
- ✅ **T14:** Edge cases volumen nulo - Validado

### Refactor Completado (Fase 0.7)
- ✅ **WidthMappingTable:** Extraída a `width_mapping.py` - Reducción de 40 líneas en `lumber_reception.py`
- ✅ **Imports actualizados:** `lumber_reception.py` importa desde módulo dedicado
- ✅ **Corrección imports:** Removidos imports problemáticos en `reception_parser.py` (pdfplumber, funciones inexistentes)
- ✅ **__init__.py:** Nuevo módulo incluido en orden de carga

---

## 🔧 ÚLTIMOS CAMBIOS VALIDADOS

### Tests Implementados (T01-T14)
- ✅ **T01:** Suma m³ por línea - Validado
- ✅ **T02:** Suma MBF por línea - Validado
- ✅ **T03:** Triple capa (Blanks) - Validado
- ✅ **T04:** Rule metric - Validado
- ✅ **T05:** Rule f1550 - Validado
- ✅ **T06:** Rule f5085 - Validado
- ✅ **T07:** Gate 2 nominal null - Validado
- ✅ **T08:** Gate 2 producto inválido - Validado
- ✅ **T09:** Gate 2 volumen tolerancia - Validado
- ✅ **T10:** Gate 3 commit - Validado
- ✅ **T11:** Recall lote trazabilidad - Validado
- ✅ **T12:** Conciliación comercial-bodega - Validado
- ✅ **T13:** Standard + Blanks convivencia - Validado
- ✅ **T14:** Edge cases volumen nulo - Validado

### Refactor Completado (Fase 0.7)
- ✅ **WidthMappingTable:** Extraída a `width_mapping.py` - Reducción de 40 líneas en `lumber_reception.py`
- ✅ **Imports actualizados:** `lumber_reception.py` importa desde módulo dedicado
- ✅ **Corrección imports:** Removidos imports problemáticos en `reception_parser.py` (pdfplumber, funciones inexistentes)
- ✅ **__init__.py:** Nuevo módulo incluido en orden de carga

### Correcciones Aplicadas
- ✅ Campos duplicados eliminados
- ✅ Validaciones de rango implementadas
- ✅ Servicio `LumberReceptionService` operativo
- ✅ Tabla `WidthMappingTable` funcional

### Cambios — 2026-05-13

#### CAMBIO A: Vista XML del wizard mass_update creada
- Archivo nuevo: `views/wizard_lumber_reception_mass_update.xml`
- `subproduct_id` con `quick_create` habilitado, `domain` sobre `allowed_subproduct_ids`
- Compatible con wizard existente en `wizard/lumber_reception_mass_update.py`

#### CAMBIO B: Selector de unidad para columna Largo
- Archivo: `models/lumber_reception.py` (lumber.reception.line)
- Campos nuevos:
  - `length_uom`: Selection (m/mm/ft, default='m') — unidad de ingreso
  - `length_input_raw`: Float — valor ingresado por operador en la unidad elegida
- Lógica: `onchange` normaliza a metros y escribe en `length` (fuente de verdad)
- Factores: mm×0.001 / ft×0.3048 / m×1.0
- `_compute_vol_shipment_m3` NO modificado — sigue leyendo `length` en metros
- Tests T01-T28: sin impacto (length sigue siendo metros)
- Tests nuevos: T29 (ft→m), T30 (mm→m), T31 (m→m sin cambio), T32 (quick-create subproducto)
- Vista: `views/lumber_reception_views.xml` — columna largo muestra `input_raw` + `uom` + `length` readonly

---

## 🚧 TRABAJO PENDIENTE CRÍTICO

### Fase 0.6 - Validación Completa
1. **T10-T14:** Implementar tests de integración completa
2. **Gate 3:** Validar commit final y creación de stock.lot/stock.picking
3. **Trazabilidad:** Cerrar riesgo package_no → lot_name

### Fase 0.7 - Refactor Monolítico (✅ INICIADO - DEUDA REMANENTE)
1. ✅ **Parser Dispatcher:** Extraído a `reception_parser.py`
2. ✅ **Stock Engine:** Extraído a `reception_service.py` 
3. ✅ **Workflow Engine:** Extraído a `reception_workflow.py`
4. ✅ **Utilidades:** Métodos puros extraídos a `mixin_lumber_ingest.py` y `utils_uom.py` (DRY)

---

## 📋 PROTOCOLO DE CONTINUIDAD

### Para modificar código:
1. **Leer este documento** - Entender estado actual
2. **Actualizar tests** - Si tocas cálculos o lógica
3. **Validar cambios** - Ejecutar tests relevantes
4. **Actualizar este documento** - Registrar cambios
5. **Commitear** - Con mensaje descriptivo

### Para agregar funcionalidad:
1. **Revisar backlog** - Ver si ya está planificado
2. **Agregar test primero** - TDD approach
3. **Implementar código** - Siguiendo arquitectura actual
4. **Actualizar documentación** - Este archivo y 00_ARQUITECTURA.md

---

## 🔍 CONTACTOS Y SOPORTE

**Estado del proyecto:** Fase 5.0 - Calidad y Ecosistema
**Próxima milestone:** Integración con Módulo de Facturación y Logística
**Riesgo principal:** Casos de uso simultáneos (Standard + Blanks en la misma guía)

**En caso de dudas:** Revisar 03_TESTS.md para casos de uso validados</content>
<parameter name="filePath">/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_core/docs/02_CONTINUIDAD.md

---

## DECISIÓN TÉCNICA 2026-05-13 - INGESTA Y UNIDADES DE LARGO

### Contexto
Se detectó una fuente de confusión funcional al mezclar la selección de perfil de ingesta con la interpretación del campo largo en `lumber.reception.line`.
La ingesta no debe pensarse solo como "métrico vs imperial", sino como perfiles de cálculo con semántica propia.

### Perfiles relevantes confirmados
- `metric`
- `s2s`
- `blanks`
- `f1550`
- `f5085`

### Regla de diseño
- El perfil de ingesta define la semántica del cálculo.
- `metric` usa lógica métrica.
- `s2s` tiene reglas propias de negocio y no debe asumirse equivalente a `metric` sin revisar fórmula.
- `blanks` convive con reglas específicas y debe mantenerse aislado para no contaminar otros cálculos.
- `f1550` y `f5085` son reglas volumétricas específicas ya validadas en la matriz de pruebas.
- Antes de introducir cambios al campo largo o a nuevas unidades, se debe mapear primero qué fórmula usa cada perfil.

### Consecuencia práctica
No implementar cambios de `length`, `length_m`, `length_raw`, `length_uom` o selector de unidades sin:
1. revisar el perfil de ingesta real usado por la línea;
2. identificar la fórmula aplicable;
3. validar convivencia con `Standard Blanks`;
4. actualizar tests y documentación.

### Estado
Pendiente de implementación controlada.
Decisión aprobada: documentar primero y luego aplicar solución mínima.

