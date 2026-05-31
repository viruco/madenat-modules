#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# MADENAT Lumber Core - Regeneración documental completa
# Alcance: SOLO DOCUMENTACIÓN
# Requiere ejecutar desde la raíz del módulo madenat_lumber_core
# ============================================================

MODULE_ROOT="$(pwd)"
DOCS_DIR="${MODULE_ROOT}/docs"
TS="$(date +%Y%m%d_%H%M%S)"
HIST_DIR="${DOCS_DIR}/historico_actual/${TS}"

if [[ ! -d "${DOCS_DIR}" ]]; then
  echo "ERROR: No existe ${DOCS_DIR}"
  echo "Ejecuta este script desde la raíz del módulo madenat_lumber_core"
  exit 1
fi

echo "============================================================"
echo " MADENAT Lumber Core - Regeneración documental"
echo "============================================================"
echo "Module root : ${MODULE_ROOT}"
echo "Docs dir    : ${DOCS_DIR}"
echo "Hist dir    : ${HIST_DIR}"
echo

mkdir -p "${HIST_DIR}"

echo "[1/6] Respaldando documentación actual..."
find "${DOCS_DIR}" -maxdepth 1 -type f -name "*.md" -print0 | while IFS= read -r -d '' f; do
  cp -a "$f" "${HIST_DIR}/"
done

if [[ -d "${DOCS_DIR}/Errores" ]]; then
  mkdir -p "${HIST_DIR}/Errores"
  find "${DOCS_DIR}/Errores" -type f -name "*.md" -print0 | while IFS= read -r -d '' f; do
    rel="${f#${DOCS_DIR}/}"
    mkdir -p "${HIST_DIR}/$(dirname "$rel")"
    cp -a "$f" "${HIST_DIR}/$rel"
  done
fi

echo "[2/6] Registrando inventario documental..."
find "${DOCS_DIR}" -type f | sort > "${HIST_DIR}/INVENTARIO_ORIGINAL.txt"

echo "[3/6] Eliminando únicamente documentos canónicos a regenerar..."
rm -f \
  "${DOCS_DIR}/00_ARQUITECTURA.md" \
  "${DOCS_DIR}/01_FLUJO_PACKING.md" \
  "${DOCS_DIR}/02_CONTINUIDAD.md" \
  "${DOCS_DIR}/03_TESTS.md" \
  "${DOCS_DIR}/04_DECISION_LOG.md" \
  "${DOCS_DIR}/05_BACKLOG.md" \
  "${DOCS_DIR}/06_CHECKLIST.md" \
  "${DOCS_DIR}/07_TRABAJO_CON_IA.md" \
  "${DOCS_DIR}/CHECKLIST_FINALIZACION.md" \
  "${DOCS_DIR}/ESTADO_MODULO.md" \
  "${DOCS_DIR}/GUIA_PRODUCCION_FINAL.md" \
  "${DOCS_DIR}/HOJA_RUTA_EJECUTIVA.md" \
  "${DOCS_DIR}/INDICE_DOCUMENTACION.md" \
  "${DOCS_DIR}/MANIFEST_ENTREGA.md" \
  "${DOCS_DIR}/QUICK_START.md" \
  "${DOCS_DIR}/RESUMEN_AUDITORIA_Y_DOCUMENTACION.md" \
  "${DOCS_DIR}/ROADMAP.md"

echo "[4/6] Reescribiendo documentos canónicos..."

cat > "${DOCS_DIR}/00_ARQUITECTURA.md" <<'EOF'
# Arquitectura — MADENAT Lumber Core

**Módulo:** `madenat_lumber_core`  
**Versión documental:** `6.0.0`  
**Fecha de actualización:** 2026-05-13  
**Estado:** ACTIVO — Arquitectura modular parcial, documentación alineada al estado real  
**Compatibilidad objetivo:** Odoo 18 CE

---

## 1. Propósito

Este módulo concentra el flujo operativo y técnico de MADENAT para recepción de madera, staging documental, análisis comercial, cálculo volumétrico, validación por gates y persistencia controlada a inventario.

Su responsabilidad principal no es solo “crear lotes”, sino garantizar que el paso desde documento origen hacia `stock.lot` ocurra con trazabilidad, consistencia matemática y control de side effects.

---

## 2. Posición en la cadena funcional

```text
madenat_lumber_shipping_core
            ↓
    madenat_lumber_core
            ↓
madenat_lumber_logistics / facturación futura
```

El módulo actúa como núcleo de ingestión, staging, validación y escritura controlada a stock.

---

## 3. Estado real de la arquitectura

La arquitectura actual es **modular parcial**. Esto significa que ya se extrajeron componentes importantes del antiguo monolito, pero todavía existe concentración funcional dentro de `models/lumber_reception.py`.

### Componentes desacoplados ya existentes
- `reception_parser.py` — Dispatcher y parseo multi-formato.
- `reception_workflow.py` — Flujo de estados y validaciones operativas.
- `reception_service.py` — Escritura a stock y servicios de persistencia.
- `mixin_lumber_ingest.py` — Lógica compartida de ingestión.
- `utils_uom.py` — Conversión y constantes volumétricas.
- `width_mapping.py` — Tabla de mapeo de anchos.

### Componente aún concentrado
- `models/lumber_reception.py` mantiene todavía:
  - `LumberReceptionLine`
  - `LumberReception`
  - computes de staging
  - parte de normalizaciones y comportamiento UI

**Conclusión arquitectónica:** el refactor estructural está avanzado y funcional, pero no está completada la separación total de línea/cabecera a archivos independientes.

---

## 4. Modelos funcionales principales

## 4.1 `lumber.reception.line`

Modelo de staging que representa la línea documental antes de Gate 3.

### Responsabilidades
- Reflejar la información cargada desde packing/documentos.
- Preservar triple capa: visual, física y nominal.
- Servir de superficie de corrección operativa previa a stock.
- Proveer base para cálculos de volumen y trazabilidad.

### Campos funcionales relevantes
- `reception_id`
- `lot_name`
- `package_no`
- `product_id`
- `subproduct_id`
- `product_code`
- `product_name`
- `pieces`
- `thickness_visual`
- `width_visual`
- `thickness`
- `width`
- `thickness_nominal`
- `width_nominal`
- `length`
- `length_uom`
- `length_input_raw`
- `vol_physical_m3`
- `vol_purchase_m3`
- `vol_shipment_m3`
- `vol_mbf`
- `export_calculation_rule`
- `audit_snapshot`
- `audit_hash`

### Nota crítica sobre largo
A partir del cambio documental del 2026-05-13 se consolida la política:
- `length` es la fuente de verdad en metros.
- `length_input_raw` conserva el valor digitado por el operador.
- `length_uom` define la unidad de entrada (`m`, `mm`, `ft`).
- La normalización debe ocurrir antes de cualquier cálculo volumétrico.

### Riesgo técnico vigente
Existe un hallazgo reciente que debe quedar trazado documentalmente: un `@depends` de `_compute_lengthm` sigue referenciando `lengthinputraw`, mientras el campo vigente documentado y esperado por vistas es `length_input_raw`. Esta discrepancia rompe la construcción del registry al instalar/actualizar el módulo y debe considerarse bug vivo de código, no de arquitectura.

---

## 4.2 `lumber.reception`

Cabecera del flujo de recepción.

### Responsabilidades
- Gestionar el estado del proceso.
- Orquestar gates y transiciones.
- Centralizar la recepción documental.
- Controlar cuándo una recepción puede procesarse, reabrirse o cancelarse.
- Vincular staging, snapshot y salida a inventario.

### Campos relevantes
- `reception_line_ids`
- `state`
- `ingestion_profile`
- `audit_snapshot`
- `audit_hash`
- `can_process_reception`
- `can_reopen_reception`
- `can_cancel_reception`
- `guia_numero`
- `guia_fecha`
- `supplier_id`
- `order_id`

---

## 4.3 `madenat.guia.processing` y líneas

Este flujo sigue siendo parte del módulo para escenarios de guía procesada, servicios y trazabilidad operativa complementaria.

### Responsabilidades
- Parsear guía de despacho.
- Integrar PDF y Excel.
- Crear staging alternativo.
- Validar consistencia.
- Transferir a stock cuando el flujo lo requiera.

---

## 5. Gates y política de side effects

## Gate 0
Validación básica de archivos y formato.  
**Regla:** no escribe stock.

## Gate 1
Conciliación documental PDF vs Excel vs OC.  
**Regla:** no escribe stock.

## Gate 2
Análisis comercial: producto, subproducto, nominales, tolerancias.  
**Regla:** no escribe stock.

## Gate 3
Snapshot final, firma SHA-256, commit de inventario y creación de lotes/movimientos.  
**Regla:** es el único punto autorizado para efectos reales en inventario.

---

## 6. Triple capa

La triple capa sigue siendo decisión estructural vigente:

- **Visual:** valor que vio el operador en el documento.
- **Física:** dato utilizable por backend y cálculos reales.
- **Nominal:** dato usado para costeo, compra y exportación.

Ninguna actualización funcional debe colapsar estas capas sin documentar la decisión.

---

## 7. Regla de largo y unidades

Se documenta formalmente la regla operativa para largo:

### Fuente de verdad
- `length` en metros.

### Campo de ingreso humano
- `length_input_raw`

### Selector semántico
- `length_uom`

### Conversión esperada
- `mm` → `length = length_input_raw * 0.001`
- `ft` → `length = length_input_raw * 0.3048`
- `m` → `length = length_input_raw`

### Implicación
Los cálculos de:
- `vol_physical_m3`
- `vol_purchase_m3`
- `vol_shipment_m3`
- `vol_mbf`

deben seguir leyendo `length` normalizado, nunca el campo crudo.

---

## 8. Relaciones con otros componentes

### Core Odoo
- `stock.lot`
- `stock.move`
- `stock.picking`
- `purchase.order`
- `product.product`
- `res.partner`
- `res.currency`
- `ir.attachment`

### Ecosistema MADENAT
- logística
- shipping
- futura integración financiera con consolidación de facturación

---

## 9. Estado de modularización

### Ya resuelto
- Parser desacoplado.
- Servicio de persistencia desacoplado.
- Helpers matemáticos desacoplados.
- Tabla de anchos separada.

### Pendiente
- Separación física de `LumberReceptionLine` hacia archivo propio.
- Adelgazamiento definitivo de `lumber_reception.py`.
- Cierre del bug de `@depends` inconsistente para largo.

---

## 10. Restricciones técnicas vigentes

- Odoo 18 CE.
- Uso de `<list>` en lugar de `<tree>` en vistas de lista.
- Sin SQL raw en producción.
- Sin fallback silencioso para tipo de cambio.
- Sin writes en Gate 0, 1 y 2.
- Documentar todo cambio estructural en `04_DECISION_LOG.md`.

---

## 11. Deuda técnica viva

| ID | Severidad | Descripción | Estado |
|---|---|---|---|
| DT-ARQ-01 | Alta | `lumber_reception.py` sigue concentrando demasiada lógica | Vigente |
| DT-ARQ-02 | Alta | Bug de `@depends` con `lengthinputraw` vs `length_input_raw` | Crítico |
| DT-ARQ-03 | Media | Constraint `stock_lot_check_cost_positive` falla en actualización | Vigente |
| DT-ARQ-04 | Media | Limpieza de warnings XML en vistas | Vigente |

---

## 12. Criterio de alineación documental

Este documento debe prevalecer sobre resúmenes antiguos.  
Si el código cambia en:
- layout de largo,
- campos de staging,
- gates,
- modularización,
- o política de side effects,

entonces este archivo debe actualizarse antes del siguiente commit.
EOF

cat > "${DOCS_DIR}/01_FLUJO_PACKING.md" <<'EOF'
# MADENAT — Flujo Integral del Packing

**Versión documental:** 4.0.0  
**Fecha de actualización:** 2026-05-13  
**Estado:** ACTIVO — Validado conceptualmente, con incidencia técnica viva en largo/unidades

---

## 1. Objetivo

Controlar el recorrido completo del packing desde documento origen hasta lote final, preservando trazabilidad, cálculos reproducibles y control estricto sobre el momento en que se escribe inventario.

---

## 2. Ruta canónica

```text
Recepción Física
    ↓
Gate 0
    ↓
Gate 1
    ↓
Staging / Espejo Documental
    ↓
Gate 2 / Análisis Comercial
    ↓
Cálculo Exportación
    ↓
Gate 3 / Snapshot + SHA-256
    ↓
Persistencia a Stock
    ↓
Auditoría
```

---

## 3. Etapa 1 — Recepción Física

### Entradas
- PDF guía
- PDF OC (opcional)
- Excel packing list

### Objetivo
Confirmar que existe base documental suficiente y legible para construir staging.

### Salida esperada
- Recepción reconocida.
- Archivos cargados.
- Ningún write real a stock.

---

## 4. Etapa 2 — Gate 0

### Qué valida
- Formato de archivo
- tamaño
- integridad mínima
- posibilidad de parseo

### Regla
Gate 0 no puede dejar efectos secundarios de inventario.

---

## 5. Etapa 3 — Gate 1

### Qué valida
- guía vs Excel
- guía vs OC
- tipo de cambio
- volumen declarado
- consistencia documental mínima

### Salida esperada
- recepción verificada
- líneas de staging creadas
- bloqueo si existe inconsistencia crítica

---

## 6. Etapa 4 — Staging / Espejo Documental

El staging es un espejo controlado del documento y no una aproximación libre.

### Debe exponer
- `package_no`
- `lot_name`
- producto
- subproducto
- piezas
- capa visual
- capa física
- capa nominal
- regla de exportación
- volúmenes

### Regla nueva de largo
El operador puede ingresar largo en:
- metros
- milímetros
- pies

pero el sistema debe convertir siempre a metros internos.

### Campos asociados
- `length_input_raw`
- `length_uom`
- `length`

### Riesgo operativo
Si el largo se ve correcto en UI pero el compute está dependiendo de un campo inexistente, la instalación del módulo se rompe antes de que el flujo pueda validarse. Por eso el problema de `lengthinputraw` vs `length_input_raw` impacta el flujo completo.

---

## 7. Etapa 5 — Análisis Comercial / Gate 2

### Valida
- producto activo
- subproducto válido
- nominales presentes
- volumen recalculado en tolerancia
- coherencia comercial del staging

### Restricción
No puede crear stock.

### Salida esperada
- staging listo para snapshot
- línea aprobable
- diferencia compra/embarque entendible

---

## 8. Etapa 6 — Cálculo de exportación

### Reglas vigentes
- `metric`
- `f1550`
- `f5085`
- perfiles adicionales según negocio

### Objetivo
Obtener volumen exportable reproducible matemáticamente.

### Regla de oro
Si un valor “parece correcto” pero no puede reproducirse, el flujo no está cerrado.

---

## 9. Etapa 7 — Gate 3

### Requisitos
- staging validado
- snapshot completo
- hash SHA-256
- autorización para persistencia

### Único lugar con write real
Gate 3 crea:
- `stock.lot`
- `stock.move`
- `stock.picking`
- vínculos de trazabilidad

---

## 10. Etapa 8 — Auditoría

### Evidencia mínima
- guía
- OC
- Excel
- usuario
- timestamp
- resumen de validaciones
- snapshot
- hash
- lotes creados
- picking creado

### Meta
Reconstruir una recepción sin depender de memoria humana.

---

## 11. Conciliaciones obligatorias

### 11.1 Documento vs staging
- líneas
- dimensiones
- package
- volumen

### 11.2 Staging vs análisis comercial
- producto
- subproducto
- nominales
- tolerancias

### 11.3 Análisis comercial vs exportación
- regla aplicada
- volumen salida
- MBF
- diferencia explicada

### 11.4 Exportación vs stock
- lot_name
- piezas
- lotes creados
- picking creado

---

## 12. Casos de error típicos

| Problema | Síntoma | Acción |
|---|---|---|
| `package_no` no propaga | lote genérico | revisar staging y servicio |
| Regla exportación mal aplicada | volumen incoherente | revisar compute |
| Nominal faltante | Gate 2 bloquea | corregir staging |
| Producto inválido | no debería confirmar | revisar catálogo |
| Tipo de cambio ausente | error financiero | bloquear |
| `lengthinputraw` en depends | falla registry | corregir código y actualizar pruebas |

---

## 13. Definición de cerrado

El flujo se considera realmente cerrado cuando:
- la ruta documental → staging → análisis → exportación → stock está trazada,
- los cálculos se reproducen,
- Gate 3 es el único write real,
- y la política de largo/unidades queda estable en código, vistas, tests y documentación.
EOF

cat > "${DOCS_DIR}/02_CONTINUIDAD.md" <<'EOF'
# MADENAT — Estado de Continuidad Técnica

**Versión documental:** 5.0.0  
**Fecha de actualización:** 2026-05-13  
**Estado:** ACTIVO — Incidencia crítica actual en instalación por `@depends` inconsistente

---

## 1. Propósito

Este documento es el checkpoint técnico vivo del proyecto.  
Debe permitir retomar el trabajo sin reconstruir el contexto desde cero.

---

## 2. Estado actual resumido

### Infraestructura
- Módulo: `madenat_lumber_core`
- Target: Odoo 18 CE
- Ambiente usual: Docker (`odoo18_app`, `db` / `odoo18_db` según stack)
- Arquitectura: modular parcial

### Estado funcional consolidado
- Gates 0 a 3 definidos documentalmente
- Suite T01–T14 consolidada en documentación
- Triple capa operativa como regla de negocio
- Servicio de persistencia y parser ya desacoplados

### Estado real actual
La actualización reciente de largo por unidad de ingreso dejó documentación y vistas alineadas hacia:
- `length_input_raw`
- `length_uom`
- `length`

pero el código aún presenta al menos una dependencia antigua a `lengthinputraw`, generando error de instalación del módulo en la construcción del registry.

---

## 3. Hallazgo crítico vigente

### Incidente activo
Durante actualización/instalación del módulo se obtiene:

```text
ValueError: Wrong @depends on '_compute_lengthm'
Dependency field 'lengthinputraw' not found in model lumber.reception.line
```

### Interpretación
No es un problema de la vista actual.  
Es un problema de coherencia entre:
- definición de campo,
- compute method,
- decorador `@depends`,
- y nombres documentados tras el cambio del 2026-05-13.

### Estado
- Documentación: alineada a `length_input_raw`
- Vista: alineada a `length_input_raw`
- Código Python: inconsistencia viva
- Instalación de módulo: bloqueada

---

## 4. Cambios documentados 2026-05-13

## Cambio A — Wizard mass update
- Se incorpora vista XML del wizard de actualización masiva.
- `subproduct_id` opera con `quick_create`.
- Debe convivir con restricciones comerciales del flujo.

## Cambio B — Largo con unidad de ingreso
- Campo nuevo: `length_uom`
- Campo nuevo: `length_input_raw`
- `length` pasa a consolidarse como valor normalizado en metros
- Factores documentados:
  - `mm = * 0.001`
  - `ft = * 0.3048`
  - `m = * 1.0`

## Cambio C — T29 a T32
Se reservan documentalmente los siguientes escenarios:
- T29: ft → m
- T30: mm → m
- T31: m → m
- T32: quick-create subproducto

**Nota:** estos escenarios están definidos documentalmente, pero no deben marcarse como cerrados mientras el bug de instalación siga abierto.

---

## 5. Estado de pruebas

### Pruebas documentadas consolidadas
- T01–T14: base estable de negocio
- T15–T28: saneamiento y blindaje documental ya registrados en matriz histórica

### Pruebas bloqueadas o no cerradas
- T29–T32 dependen de resolver primero la inconsistencia del `@depends`

---

## 6. Prioridades inmediatas

### Prioridad 1 — Reparar instalación
Buscar y corregir todas las referencias antiguas:
- `lengthinputraw`
- `lengthuom`
- y cualquier compute asociado a `_compute_lengthm`

### Prioridad 2 — Revalidar upgrade
Ejecutar:
- limpieza de `__pycache__` dentro del addon
- update del módulo en DB de prueba
- validación de carga de vistas y registry

### Prioridad 3 — Cerrar documentalmente T29–T32
Solo después de resolver la instalación:
- ajustar matriz de tests
- cerrar continuidad
- actualizar checklist de finalización

---

## 7. Riesgos activos

| Riesgo | Severidad | Estado |
|---|---|---|
| `@depends` roto para largo | Crítica | Abierto |
| Constraint `stock_lot_check_cost_positive` | Alta | Abierto |
| Modelo financiero ausente | Alta | Abierto |
| Warnings XML menores | Media | Abierto |
| Monolito parcial en `lumber_reception.py` | Media | Abierto |

---

## 8. Qué tocar y qué no tocar

### Sí tocar
- documentación canónica
- compute y depends de largo
- tests de largo
- continuidad y decisión técnica

### No tocar aún
- arquitectura global congelada
- refactor grande de separación de archivos
- Fase 6 financiera antes de estabilizar instalación

---

## 9. Punto de retoma recomendado

1. Hacer grep de `lengthinputraw`, `length_input_raw`, `lengthuom`, `length_uom`, `_compute_lengthm`.
2. Corregir compute y decoradores.
3. Volver a correr upgrade con `-u madenat_lumber_core`.
4. Si instala, ejecutar T29–T32.
5. Solo entonces retomar backlog financiero.

---

## 10. Regla de oro de continuidad

Si se modifica:
- naming de campos,
- unidad de largo,
- computes,
- o contratos de Gate 2/Gate 3,

este documento debe actualizarse antes del siguiente checkpoint.
EOF

cat > "${DOCS_DIR}/03_TESTS.md" <<'EOF'
# MADENAT — Matriz de Pruebas

**Versión documental:** 6.0.0  
**Fecha de actualización:** 2026-05-13  
**Estado:** ACTIVO — Base T01–T14 consolidada; T29–T32 definidos pero no cerrados

---

## 1. Regla operativa

Toda modificación de parser, staging, cálculos, units-of-measure, gates o persistencia debe quedar registrada aquí antes de considerarse realmente cerrada.

---

## 2. Matriz principal consolidada

| ID | Caso | Entrada | Esperado | Estado documental |
|---|---|---|---|---|
| T01 | Suma m3 por línea | Packing estándar | Suma líneas = total recepción | CERRADO |
| T02 | Suma MBF por línea | Packing estándar | MBF consistente | CERRADO |
| T03 | Triple capa | Blanks | Visual, física y nominal correctas | CERRADO |
| T04 | Regla `metric` | Línea nacional | `vol_shipment_m3 = vol_physical_m3` | CERRADO |
| T05 | Regla `f1550` | Línea S2S | cálculo exacto con factor oficial | CERRADO |
| T06 | Regla `f5085` | Línea Blanks | cálculo exacto con factor oficial | CERRADO |
| T07 | Gate 2 nominal null | Staging incompleto | bloquea confirmación | CERRADO |
| T08 | Gate 2 producto inválido | producto inactivo | bloquea confirmación | CERRADO |
| T09 | Gate 2 volumen fuera tolerancia | diferencia excesiva | bloquea confirmación | CERRADO |
| T10 | Gate 3 commit | staging válido | crea stock y picking | CERRADO |
| T11 | Recall de lote | recepción cerrada | trazabilidad por lote/paquete | CERRADO |
| T12 | Conciliación comercial-bodega | recepción cerrada | lotes = líneas aprobadas | CERRADO |
| T13 | Standard + Blanks | recepción mixta | sin contaminación entre reglas | CERRADO |
| T14 | Edge cases volumen nulo | dimensiones inválidas | bloqueo | CERRADO |

---

## 3. Matriz de saneamiento ya consolidada

| ID | Caso | Objetivo | Estado documental |
|---|---|---|---|
| T15 | Campos duplicados eliminados | evitar shadowing | CERRADO |
| T16 | `@api.depends` consolidados | eliminar duplicidad | CERRADO |
| T17 | Importaciones reparadas | estabilidad de parser | CERRADO |
| T18 | Variables indefinidas corregidas | flujo robusto | CERRADO |
| T19 | Métodos incompletos completados | base operativa | CERRADO |
| T20 | `WidthMappingTable` funcional | mapeo anchos | CERRADO |
| T21 | `LumberReceptionService` operativo | persistencia desacoplada | CERRADO |
| T22 | Validaciones de rango | calidad de datos | CERRADO |
| T23 | Validaciones de dimensiones | blindaje físico | CERRADO |
| T24 | Pruebas unitarias extendidas | cobertura adicional | CERRADO |
| T25 | Tests Docker | instalación controlada | CERRADO |
| T26 | Staging → stock.lot | persistencia real | CERRADO |
| T27 | Validaciones en create/write | integridad | CERRADO |
| T28 | Cálculos blindados | precisión 3 decimales | CERRADO |

---

## 4. Matriz nueva por largo/unidades

| ID | Caso | Entrada | Esperado | Estado documental |
|---|---|---|---|---|
| T29 | Conversión ft → m | `length_input_raw` en pies | `length` normalizado a metros | PENDIENTE |
| T30 | Conversión mm → m | `length_input_raw` en mm | `length` normalizado a metros | PENDIENTE |
| T31 | Conversión m → m | `length_input_raw` en m | `length` sin alteración | PENDIENTE |
| T32 | Quick-create subproducto | wizard mass update | alta rápida funcional | PENDIENTE |

### Bloqueante común
Ninguno de estos casos puede considerarse cerrado mientras la instalación falle por `Wrong @depends` en `_compute_lengthm`.

---

## 5. Caso base recomendado

- Guía: `40597`
- OC: `MC2603-306`
- Volumen PDF: `55.665 m³`
- Volumen Excel: `55.821 m³`
- Uso: validación integral de staging, cálculo y persistencia

---

## 6. Plantilla de ejecución

```md
### Caso: TXX
- Fecha:
- Operador:
- Ambiente:
- Base de datos:
- Rama / commit:
- Input:
- Esperado:
- Real:
- Logs:
- Evidencia:
- Estado:
- Hallazgos:
```

---

## 7. Criterios globales de aprobación

- 0 writes en Gate 0, 1 y 2
- 0 SQL raw en producción
- solo Gate 3 escribe inventario
- cálculos reproducibles
- trazabilidad desde `package_no` a `lot_name`
- coherencia de naming entre campos, vistas y `@depends`

---

## 8. Lectura rápida de fallos

| Si falla | Revisar |
|---|---|
| T01 / T02 | parser, unidades, sumatorias |
| T03 | staging y triple capa |
| T04 / T05 / T06 | reglas de exportación |
| T07 / T08 / T09 | Gate 2 y catálogo |
| T10 | Gate 3 y servicio stock |
| T11 / T12 | trazabilidad |
| T13 | dispatcher multi-formato |
| T14 | validaciones de edge |
| T29 / T30 / T31 | naming de largo, normalización y computes |
| T32 | wizard, domain y quick-create |

---

## 9. Regla documental final

Una prueba no queda cerrada porque “parece funcionar”.  
Queda cerrada cuando:
- existe esperado explícito,
- existe resultado real,
- hay evidencia,
- y continuidad + backlog quedan actualizados si el hallazgo cambia el estado del proyecto.
EOF

cat > "${DOCS_DIR}/04_DECISION_LOG.md" <<'EOF'
# 04 — Decision Log

**Módulo:** MADENAT Lumber Core  
**Versión documental:** 6.0.0  
**Última actualización:** 2026-05-13  
**Estado:** Canonical / activo

---

## Propósito

Registrar las decisiones técnicas que gobiernan arquitectura, flujo funcional, trazabilidad y continuidad.

---

## 2026-04-08 — Cimentación

### AD-01 — Base documental canónica única
Se define una base documental central para evitar versiones parciales incompatibles.

### AD-02 — Foco en flujo integral y matemática reproducible
La validación del módulo se centra en que documento, staging, exportación y stock puedan reconciliarse matemáticamente.

### AD-03 — Regla de menús
Los menús viven en árbol principal; las vistas describen interiores.

### AD-04 — Gate 3 como único write real
Gate 3 es el único punto autorizado para escribir inventario real.

### AD-05 — Tipo de cambio explícito
Se prohíben fallbacks silenciosos para TC.

### AD-06 — Protocolo de colaboración con IA
La continuidad se apoya en cápsulas breves y actualización dirigida de archivos.

---

## 2026-05-03 — Modularización y estabilidad

### AD-07 — Desacoplamiento parcial del monolito
Se extrae parser, workflow, servicio y helpers, pero se acepta temporalmente que `lumber_reception.py` siga concentrando clases principales.

### AD-08 — Lógica compartida en mixins/helpers
Se consolida reutilización de cálculos y utilidades para evitar reglas divergentes.

### AD-09 — Base T01–T14 como núcleo estable
Se toma la suite T01–T14 como el corazón funcional validado del proyecto.

### AD-10 — Fase 6 financiera como siguiente frente mayor
Una vez estabilizada la base, el siguiente frente es `lumber.billing.consolidation.line`.

---

## Compatibilidad Odoo 18

### AD-11 — Uso de `<list>`
En Odoo 18 las vistas de lista deben declararse con `<list>`.

---

## 2026-05-13 — Largo con unidad de ingreso

### AD-12 — `length` en metros como fuente de verdad
Se define formalmente que `length` es el valor interno canónico para cálculos.

### AD-13 — `length_input_raw` como preservación de entrada humana
Se agrega el concepto de valor crudo de ingreso para no perder la semántica del operador.

### AD-14 — `length_uom` desacoplado del perfil de ingesta
La unidad de largo no debe confundirse con el perfil de cálculo. Son conceptos distintos.

### AD-15 — Los cálculos deben leer valor normalizado
Todos los computes volumétricos deben basarse en `length` ya convertido.

### AD-16 — No cerrar T29–T32 sin estabilidad de instalación
La mera existencia de vista/documentación no valida el feature. Si el registry falla por `@depends`, el cambio sigue abierto.

### AD-17 — La incoherencia de naming es bug crítico
Toda discrepancia entre:
- nombre de campo,
- nombre usado en vista,
- nombre usado en `@depends`,
- nombre usado en tests,

se considera bug de primer nivel porque rompe instalación o produce cómputos erróneos.

---

## Riesgos registrados

| ID | Riesgo | Mitigación |
|---|---|---|
| R-01 | Integración financiera ausente | abordar Fase 6 después de estabilizar instalación |
| R-02 | Warnings XML | limpieza progresiva |
| R-03 | Tolerancias matemáticas no formalizadas | parametrización futura |
| R-04 | Monolito parcial | refactor posterior |
| R-05 | `lengthinputraw` vs `length_input_raw` | corrección inmediata de código y revalidación |

---

## Prioridad actual

### Prioridad 0
Reparar coherencia del feature de largo/unidades para permitir instalación limpia del módulo.

### Prioridad 1
Revalidar T29–T32 tras reparación.

### Prioridad 2
Retomar Fase 6 financiera.

---

## Regla de mantenimiento

Toda decisión que cambie:
- naming de campos,
- política de cálculo,
- gates,
- o arquitectura,

debe reflejarse aquí el mismo día.
EOF

cat > "${DOCS_DIR}/05_BACKLOG.md" <<'EOF'
# MADENAT — Backlog Canónico

**Versión documental:** 6.0.0  
**Fecha de actualización:** 2026-05-13  
**Estado:** ACTIVO — Prioridad inmediata en reparación del feature largo/unidades

---

## FASE 0.5 — SANEAMIENTO CRÍTICO
- [x] Eliminación de campos duplicados
- [x] Consolidación de decoradores
- [x] Reparación de importaciones
- [x] Métodos base completados
- [x] Tabla centralizada de anchos
- [x] Servicio de recepción desacoplado
- [x] Validaciones de rango
- [x] Base T01–T14 consolidada

---

## FASE 1 — GATES Y BLINDAJE
- [x] Gate 0
- [x] Gate 1
- [x] Gate 2
- [x] Gate 3
- [x] Snapshot SHA-256
- [x] Write único en Gate 3

---

## FASE 2 — MULTIFORMATO Y TRIPLE CAPA
- [x] Dispatcher Standard / Blanks
- [x] Triple capa
- [x] Espejo documental
- [x] Regla de exportación por línea

---

## FASE 3 — FLUJO DE PACKING
- [x] Ruta documental → staging → bodega
- [x] Conciliación volumétrica
- [x] Propagación `package_no`
- [x] Picking controlado

---

## FASE 4 — REFACTOR MODULAR
- [x] Parser extraído
- [x] Workflow extraído
- [x] Servicio stock extraído
- [x] Helpers/mixins extraídos
- [ ] Separación final de `LumberReceptionLine` a archivo propio

---

## FASE 5 — CALIDAD Y ESTABILIDAD
- [x] Matriz T01–T14 consolidada
- [x] Saneamiento documental T15–T28
- [ ] Formalizar tolerancias por tipo de madera
- [ ] Limpiar warnings XML
- [ ] Resolver constraint `stock_lot_check_cost_positive`

---

## FASE 5.1 — LARGO Y UNIDADES
**Nueva prioridad operativa inmediata**

### Objetivo
Cerrar correctamente el feature de ingreso de largo con unidad seleccionable sin romper instalación.

### Tareas
- [ ] Localizar todas las referencias a `lengthinputraw`
- [ ] Sustituir por `length_input_raw` donde corresponda
- [ ] Revisar referencias a `lengthuom` / `length_uom`
- [ ] Alinear compute `_compute_lengthm`
- [ ] Reinstalar / actualizar módulo sin error de registry
- [ ] Ejecutar T29 ft→m
- [ ] Ejecutar T30 mm→m
- [ ] Ejecutar T31 m→m
- [ ] Ejecutar T32 quick-create subproducto
- [ ] Actualizar continuidad y checklist final tras validación real

### Criterio de cierre
La fase solo cierra cuando el módulo instala correctamente y T29–T32 quedan evidenciados.

---

## FASE 6 — INTEGRACIÓN FINANCIERA
**Siguiente frente mayor, pero NO antes de estabilizar Fase 5.1**

### Objetivo
Crear `lumber.billing.consolidation.line` y vincular recepciones con costeo y facturación.

### Pendientes
- [ ] Modelo `lumber.billing.consolidation.line`
- [ ] Relación con `stock.lot`
- [ ] Relación con recepción
- [ ] Subtotales / prorrateo
- [ ] Integración contable
- [ ] Reporting financiero por guía/shipment

---

## RIESGOS ACTIVOS

| Riesgo | Severidad | Acción | Estado |
|---|---|---|---|
| Bug `@depends` largo | Crítica | corregir naming y computes | ABIERTO |
| Constraint costo positivo | Alta | revisar data/modelo | ABIERTO |
| Fase 6 ausente | Alta | implementar modelo financiero | ABIERTO |
| Monolito parcial | Media | refactor futuro | ABIERTO |
| Tolerancias no formalizadas | Media | parametrizar | ABIERTO |

---

## REGLA DE PRIORIZACIÓN

No abrir un frente mayor nuevo mientras:
- el módulo no instale limpio,
- el feature de largo/unidades siga roto,
- o T29–T32 no estén validados.
EOF

cat > "${DOCS_DIR}/06_CHECKLIST.md" <<'EOF'
# MADENAT — Checklist Operativo

**Versión documental:** 4.0.0  
**Fecha de actualización:** 2026-05-13

---

## 1. Inicio de sesión
- [ ] Leer `02_CONTINUIDAD.md`
- [ ] Confirmar task activa del backlog
- [ ] Confirmar BD, rama, contenedores y módulo
- [ ] Verificar si el foco es documentación, bugfix o validación
- [ ] No abrir más de un frente mayor

---

## 2. Restricciones técnicas
- [ ] Odoo 18 CE
- [ ] XML con `<list>`
- [ ] Sin SQL raw
- [ ] Sin fallback silencioso para tipo de cambio
- [ ] Sin writes en Gate 0, 1 y 2
- [ ] `length` debe permanecer en metros como fuente de verdad

---

## 3. Flujo packing
- [ ] Validar recepción física
- [ ] Validar Gate 0
- [ ] Validar Gate 1
- [ ] Validar staging
- [ ] Validar Gate 2
- [ ] Validar cálculo de exportación
- [ ] Validar Gate 3
- [ ] Validar auditoría

---

## 4. Cálculos y unidades
- [ ] Revisar m3 físico
- [ ] Revisar m3 compra
- [ ] Revisar m3 embarque
- [ ] Revisar MBF
- [ ] Revisar tolerancias
- [ ] Revisar naming de largo
- [ ] Revisar conversión `mm/ft/m → length`

---

## 5. Validación del bug actual
- [ ] Buscar `lengthinputraw`
- [ ] Buscar `length_input_raw`
- [ ] Buscar `lengthuom`
- [ ] Buscar `length_uom`
- [ ] Revisar `_compute_lengthm`
- [ ] Confirmar instalación limpia del módulo

---

## 6. Pruebas
- [ ] Registrar caso
- [ ] Ejecutar prueba
- [ ] Guardar evidencia
- [ ] Marcar estado
- [ ] Anotar hallazgos
- [ ] Actualizar continuidad si cambia el estado real

---

## 7. Cierre de sesión
- [ ] Actualizar continuidad
- [ ] Actualizar backlog
- [ ] Actualizar decision log si cambió una regla
- [ ] Dejar próximos 3 pasos
- [ ] Dejar punto exacto de retoma
EOF

cat > "${DOCS_DIR}/07_TRABAJO_CON_IA.md" <<'EOF'
# MADENAT — Protocolo de Trabajo con IA

**Versión documental:** 5.0.0  
**Fecha de actualización:** 2026-05-13  
**Estado:** ACTIVO

---

## 1. Objetivo

Trabajar con IA sin repetir arquitectura completa, pero sin perder precisión técnica ni trazabilidad documental.

---

## 2. Regla principal

No reexplicar todo si no cambió, pero sí declarar siempre:
- fase actual
- task activa
- objetivo puntual
- ambiente
- base de datos
- módulo
- archivos a tocar
- archivos prohibidos
- evidencia
- salida esperada

---

## 3. Jerarquía de contexto

| Nivel | Contenido | Cuándo se envía |
|---|---|---|
| 1 | Arquitectura estable | Solo si cambió |
| 2 | Checkpoint operativo | En cada sesión |
| 3 | Caso puntual | Cuando aplica |
| 4 | Feedback estructurado | Después de cada iteración |

---

## 4. Cápsula mínima recomendada

```md
## SESIÓN MADENAT

### Contexto activo
- Fase:
- Task:
- Objetivo:
- Prioridad:

### Ambiente
- Odoo:
- Base de datos:
- Rama / commit:
- Contenedores:
- Módulo:

### Alcance
- Tocar:
- No tocar:

### Evidencia
- Caso:
- Hallazgo actual:
- Riesgo actual:

### Tipo de ayuda
- analizar / proponer / actualizar / paso a paso / consolidar

### Salida esperada
- explicación
- diff
- archivos completos
- checklist
- próximos pasos
```

---

## 5. Regla de actualización por archivo

| Si cambia esto | Archivos a actualizar |
|---|---|
| Foco actual | continuidad + backlog |
| Regla técnica | arquitectura + decision log |
| Flujo operativo | flujo packing + continuidad |
| Cálculo o naming de campos | arquitectura + tests + decision log + continuidad |
| Se cierra una task | backlog + continuidad |
| Riesgo nuevo | continuidad + backlog |
| Forma de colaborar con IA | este archivo |

---

## 6. Regla especial para bugs de naming

Si el bug involucra diferencias entre:
- nombre Python,
- nombre XML,
- nombre en tests,
- nombre documentado,

entonces no basta con arreglar código.  
También hay que actualizar:
- `00_ARQUITECTURA.md`
- `02_CONTINUIDAD.md`
- `03_TESTS.md`
- `04_DECISION_LOG.md`
- `05_BACKLOG.md`

---

## 7. Modos de salida válidos

- explicación primero
- diff y luego archivos
- archivos completos listos para pegar
- paso a paso
- consolidación documental completa

---

## 8. Criterio de éxito

Una sesión se considera bien ejecutada cuando:
- el foco queda claro rápido,
- los cambios aterrizan en los archivos correctos,
- el estado del proyecto queda consistente,
- y el siguiente punto de retoma es explícito.
EOF

cat > "${DOCS_DIR}/CHECKLIST_FINALIZACION.md" <<'EOF'
# MADENAT — Checklist Final de Cierre / Retoma

**Versión documental:** 6.0.0  
**Fecha de actualización:** 2026-05-13  
**Estado:** ACTIVO — No marcar como listo para producción mientras persista el bug de instalación

---

## 1. Pre-check de ambiente
- [ ] Contenedores activos
- [ ] Base accesible
- [ ] Ruta del módulo correcta
- [ ] Código sincronizado
- [ ] Documentación canónica actualizada

---

## 2. Pre-check técnico
- [ ] Sin errores de sintaxis
- [ ] Imports resuelven
- [ ] Módulo actualiza sin fallar registry
- [ ] Vistas cargan correctamente
- [ ] No hay `Wrong @depends`

---

## 3. Pruebas mínimas obligatorias
- [ ] T01–T14 cerradas o revalidadas según contexto
- [ ] T29 ft→m validada
- [ ] T30 mm→m validada
- [ ] T31 m→m validada
- [ ] T32 quick-create subproducto validada

---

## 4. Validaciones de negocio
- [ ] Gate 0 sin side effects
- [ ] Gate 1 sin side effects
- [ ] Gate 2 sin side effects
- [ ] Gate 3 como write único
- [ ] Trazabilidad `package_no → lot_name`
- [ ] Snapshot SHA-256 consistente

---

## 5. Riesgos que impiden cierre
- [ ] Bug `lengthinputraw` vs `length_input_raw`
- [ ] Constraint costo positivo
- [ ] Warnings XML críticos
- [ ] Fase financiera sin implementar

---

## 6. Criterio de “listo para continuar”
Se puede retomar desarrollo normal cuando:
- el módulo instala,
- no falla registry,
- la documentación está alineada,
- y el backlog vuelve a priorizar Fase 6.

---

## 7. Criterio de “listo para validar”
Se puede declarar listo para validación funcional cuando:
- T01–T14 siguen firmes,
- T29–T32 están evidenciadas,
- y no quedan bugs de naming en computes ni vistas.
EOF

cat > "${DOCS_DIR}/ESTADO_MODULO.md" <<'EOF'
# Estado del Módulo — MADENAT Lumber Core

**Fecha:** 2026-05-13  
**Estado global:** AMARILLO / BLOQUEADO PARCIALMENTE  
**Razón:** El módulo conserva una inconsistencia crítica en `@depends` del feature de largo con unidad.

---

## 1. Qué está estable
- arquitectura modular parcial
- gates documentados
- base T01–T14 consolidada
- parser y service desacoplados
- política de Gate 3 como write único

---

## 2. Qué está bloqueando
- `ValueError` por dependencia a `lengthinputraw`
- inconsistencia entre vista/documentación/código
- instalación no limpia del módulo

---

## 3. Qué no debe asumirse
No debe asumirse que el feature de largo/unidades está cerrado solo porque:
- existen campos documentados,
- existe vista,
- o existe intención de tests.

Mientras el módulo no instale limpio, el feature sigue abierto.

---

## 4. Siguiente acción correcta
Corregir naming y depends del compute de largo, reinstalar el módulo y ejecutar T29–T32.

---

## 5. Prioridad posterior
Retomar Fase 6 financiera únicamente después de estabilizar la base.
EOF

cat > "${DOCS_DIR}/GUIA_PRODUCCION_FINAL.md" <<'EOF'
# Guía de Producción / Validación Final

**Versión documental:** 6.0.0  
**Fecha:** 2026-05-13  
**Estado:** NO LISTO PARA PRODUCCIÓN

---

## 1. Motivo

El módulo no debe marcarse como listo para producción mientras exista error de instalación por `Wrong @depends`.

---

## 2. Secuencia correcta antes de producción

1. Corregir compute de largo.
2. Actualizar módulo sin error.
3. Ejecutar pruebas base.
4. Ejecutar pruebas nuevas de largo.
5. Revisar warnings y constraints.
6. Solo entonces preparar deploy.

---

## 3. Comandos de referencia

### Update de prueba
```bash
docker exec -it odoo18_app bash -lc "
odoo -u madenat_lumber_core -d madenattest \
--db_host=db --db_user=odoo --db_password=odoo \
--xmlrpc-port=8072 --test-enable --stop-after-init \
--log-level=test
"
```

### Búsqueda de naming roto
```bash
grep -RniE "lengthinputraw|length_input_raw|lengthuom|length_uom|_compute_lengthm" models wizard tests views
```

---

## 4. Regla de deploy

Sin instalación limpia, no hay deploy.  
Sin T29–T32 validadas, no hay cierre del feature de largo.
EOF

cat > "${DOCS_DIR}/HOJA_RUTA_EJECUTIVA.md" <<'EOF'
# Hoja de Ruta Ejecutiva — MADENAT Lumber Core

**Fecha:** 2026-05-13

---

## Estado actual
El proyecto mantiene una base funcional fuerte, pero hoy la prioridad ejecutiva no es agregar features, sino cerrar una regresión crítica en el feature de largo/unidades.

---

## Prioridades por orden

1. Reparar instalación del módulo.
2. Validar T29–T32.
3. Limpiar deuda técnica inmediata.
4. Retomar Fase 6 financiera.

---

## Resultado esperado de la semana
- módulo instalando limpio
- continuidad actualizada
- backlog reabierto sobre consolidación financiera
EOF

cat > "${DOCS_DIR}/INDICE_DOCUMENTACION.md" <<'EOF'
# Índice de Documentación — MADENAT Lumber Core

## Documentos canónicos
- `00_ARQUITECTURA.md`
- `01_FLUJO_PACKING.md`
- `02_CONTINUIDAD.md`
- `03_TESTS.md`
- `04_DECISION_LOG.md`
- `05_BACKLOG.md`
- `06_CHECKLIST.md`
- `07_TRABAJO_CON_IA.md`

## Documentos operativos
- `CHECKLIST_FINALIZACION.md`
- `ESTADO_MODULO.md`
- `GUIA_PRODUCCION_FINAL.md`
- `HOJA_RUTA_EJECUTIVA.md`
- `QUICK_START.md`
- `ROADMAP.md`
- `RESUMEN_AUDITORIA_Y_DOCUMENTACION.md`
- `MANIFEST_ENTREGA.md`

## Histórico
- `docs/historico_actual/<timestamp>/`
EOF

cat > "${DOCS_DIR}/MANIFEST_ENTREGA.md" <<'EOF'
# Manifest de Entrega Documental

**Fecha:** 2026-05-13

## Entrega incluida
- respaldo completo de markdown previo en `docs/historico_actual/<timestamp>/`
- regeneración de documentos canónicos
- alineación al hallazgo actual del feature de largo/unidades
- no se modificó código ni XML desde este script

## Objetivo
Dejar base documental coherente para continuar corrección técnica sin mezclar estados contradictorios.
EOF

cat > "${DOCS_DIR}/QUICK_START.md" <<'EOF'
# Quick Start — Retoma rápida

## 1. Leer primero
1. `02_CONTINUIDAD.md`
2. `05_BACKLOG.md`
3. `03_TESTS.md`

## 2. Buscar el bug actual
```bash
grep -RniE "lengthinputraw|length_input_raw|lengthuom|length_uom|_compute_lengthm" models wizard tests views
```

## 3. Corregir y revalidar
- alinear naming
- actualizar módulo
- ejecutar T29–T32

## 4. Recién después
retomar Fase 6 financiera
EOF

cat > "${DOCS_DIR}/RESUMEN_AUDITORIA_Y_DOCUMENTACION.md" <<'EOF'
# Resumen de Auditoría y Documentación

**Fecha:** 2026-05-13

La documentación fue consolidada para reflejar el estado real actual del proyecto:
- arquitectura modular parcial
- núcleo T01–T14 estable
- Fase 6 financiera pendiente
- bug crítico vigente en `@depends` de largo/unidades

El objetivo de esta consolidación es eliminar contradicciones entre documentos anteriores y dejar un punto único de retoma.
EOF

cat > "${DOCS_DIR}/ROADMAP.md" <<'EOF'
# Roadmap — MADENAT Lumber Core

## Corto plazo
- Reparar inconsistencia `lengthinputraw` / `length_input_raw`
- Validar T29–T32
- Limpiar constraint y warnings prioritarios

## Mediano plazo
- Implementar `lumber.billing.consolidation.line`
- Integración contable
- Reporting financiero

## Largo plazo
- Separación total de `lumber_reception.py`
- parametrización formal de tolerancias
- endurecimiento de calidad y performance
EOF

echo "[5/6] Generando bitácora de actualización..."
cat > "${HIST_DIR}/README_HISTORICO.txt" <<EOF
Respaldo generado automáticamente.
Fecha: ${TS}
Origen: ${DOCS_DIR}

Este directorio contiene copia de los markdown previos a la regeneración documental.
EOF

echo "[6/6] Listado final de documentos..."
find "${DOCS_DIR}" -maxdepth 1 -type f -name "*.md" | sort

echo
echo "============================================================"
echo " OK - Documentación regenerada"
echo " Respaldo disponible en: ${HIST_DIR}"
echo "============================================================"