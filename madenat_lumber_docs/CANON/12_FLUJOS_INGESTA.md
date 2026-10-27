# CANON/12_FLUJOS_INGESTA — Flujos de Ingesta de Madera y Discriminación Operativa

**Proyecto:** MADENAT Lumber — Odoo 18 CE  
**Versión documental:** 1.22.0
**Fecha de actualización:** 2026-10-27  <!-- 2026-10-27: §13.6 Descarte de fila de totales de cierre sin etiqueta en extract_document (Regla V1 / AD-136 / Fase 2E), eliminación de doble conteo de volumen y alineación de vista previa. Versión 1.21.0 → 1.22.0. | Fase 2E. -->
<!-- 2026-10-26: **Consolidación documental FASE 2 (E1)** — sincronización de la cabecera con la fila del índice, que ya declaraba 1.21.0 / 2026-10-26 al registrar §13 (AD-134) en `1c14206`. Sin cambio de contenido. Sin push ni despliegue. | FASE 2. -->
<!-- 2026-10-21: §12.8 Asistente de importación de consolidación de tarjas desde Excel con doble bloque y filas pendientes (AD-133 / Bloque 7.2). Versión 1.19.0 → 1.20.0. | Bloque 7. -->
<!-- 2026-10-21: §12.7 Flujo de edición de dimensiones antes y después del envío a stock (AD-132 / Bloque H5). Versión 1.18.0 → 1.19.0. | Bloque H5. -->
<!-- 2026-10-20: Incorporación de tabla sinóptica ejecutiva al inicio del documento en Bloque H0 (AD-128). Versión 1.17.0 → 1.18.0. | Bloque H0. -->
<!-- 2026-10-19: §3.3 Cita explícita de ADRs (AD-65, AD-79, AD-80, AD-87) en matriz de ingesta y formalización de Bloque 6 (AD-127). Versión 1.16.0 → 1.17.0. | Bloque 6. -->\

### Resumen Ejecutivo de Flujos de Ingesta (Tabla Sinóptica)

| Tipo de Ingesta | Discriminador (`stock.lot`) | Vía / Modelo de Entrada | Destino Inventario | Volumen Oficial |
| :--- | :--- | :--- | :--- | :--- |
| **Producto (Compra Directa)** | `reception_id` poblado | `lumber.reception` (Gate0/Gate1) | Patio de almacenamiento | F1 Nominal Compra (`volume_purchase_m3`) |
| **Procesado (Maquila / Servicio)** | `volume_source_guia_id` poblado | `madenat.guia.processing` (Excel crudo) | Patio de servicio / Procesador | F1 Nominal Compra |
| **Consolidación Administrativa** | `consolidation_id` / SV | `lumber.consolidation` (tercera vía) | Balance de masa / Consumo | F1 Nominal Compra |
| **Blanks (F6)** | Directo a stock sin Gate dim. | `lumber.reception` | Ubicación interna directa | F1 Nominal Compra (sin 1/16") |
| **Retorno de Procesador** | Imputación etiqueta → SV | `madenat.processor.return.link` | Patio asignado | F1 / F2 según despacho |

---
**Estado:** ACTIVO — Documenta la jerarquía del volumen oficial y el bloque SV visible de la Consola, el ciclo de vida controlado de guías (Modos A–D) de la Fase 2 (AD-80), la **imputación SV (etiqueta→SV)** como vía oficial del retorno procesado (§11.8, AD-87) y las reglas operativas de Blanks y Patios (§12, AD-116/AD-117).
**Fecha:** 2026-09-26\
**Estado:** ✅ Vigente — Documento canónico de flujos de ingesta (corregido: `reception_id` como discriminador operativo; §11 consolidación administrativa como tercera vía complementaria — AD-65; §11.5 política de volumen oficial de Recepción por Volumen — AD-79; §11.6 alcance del gate dimensional del core en flujos de Volumen — cierre T2 2026-09-26)\
**Responsable de actualización:** Arquitecto / Tech Lead

---

## 1. Propósito

Definir cómo ingresan los lotes al sistema MADENAT, cómo se discriminan por origen y cómo deben ser consumidos por reportes y procesos de consolidación.

Este documento es la **fuente única de verdad** para determinar el origen de un lote (`stock.lot`) dentro del sistema. Cualquier reporte, consolidación o consulta que necesite distinguir el origen de un lote debe regirse por las reglas aquí definidas.

---

## 2. Modelo de discriminación

El modelo `stock.lot` (extendido en `StockLotExtended`, `madenat_lumber_core`) expone dos campos Many2one **mutuamente excluyentes** que actúan como discriminadores de origen:

| Campo | Apunta a | Significado |
|---|---|---|
| `guia_processing_id` | `madenat.guia.processing` | Lote originado en flujo de guía procesada |
| `reception_id` | `lumber.reception` | Lote originado en flujo de recepción directa |

### Constraint de exclusividad

```python
@api.constrains('reception_id', 'guia_processing_id')
def _check_reception_guia_exclusivity(self):
    for lot in self:
        if lot.reception_id and lot.guia_processing_id:
            raise ValidationError(_(
                "Un lote no puede pertenecer simultáneamente a una "
                "recepción directa y a una guía de procesamiento."
            ))
```

**Regla canónica**: un lote pertenece a un solo flujo de ingesta. No puede tener ambos discriminadores poblados simultáneamente.

> **Nota técnica — campo legacy `lumber_reception_id`:**  
> El modelo `stock.lot` conserva el campo `lumber_reception_id` por compatibilidad histórica. Este campo no es usado por la lógica operativa actual (métodos `_compute_reception_type`, `_check_reception_guia_exclusivity`, `_compute_guia_number`, `_compute_purchase_info`, `_compute_vol_shipment_m3`) ni por los reportes activos auditados. Se considera **legacy/huérfano**.  
> El campo canónico operativo del flujo de recepción directa es **`reception_id`**.  
> **No debe usarse `lumber_reception_id` en nuevos reportes, reglas de negocio ni desarrollos.**
> 
> **Nota técnica — migración picking layer (2026-06-16):**  
> El modelo `stock.picking` fue migrado para usar `reception_id` como campo canónico almacenado. `lumber_reception_id` en `stock.picking` es ahora un campo `related` que apunta a `reception_id`, manteniendo compatibilidad de lectura/UI sin escritura operativa redundante. Ver sección 10.

---

## 3. Flujo 1 — Guía procesada (`madenat_guia_processing`)

### 3.1 Origen funcional

Flujo de ingesta de madera que ya ha pasado por un proceso de maquila, transformación o servicio externo. La madera ingresa al inventario con un grado de procesamiento previo, documentado mediante una guía de despacho de procesamiento.

### 3.2 Tablas involucradas

| Rol | Modelo | Tabla |
|---|---|---|
| Origen | `madenat.guia.processing` | Cabecera de guía de procesamiento |
| Origen (líneas) | `madenat.guia.processing.line` | Líneas de detalle de la guía |
| Destino | `stock.lot` | Lote de inventario |

### 3.3 Campo discriminador y Matriz Operativa de Ingesta (AD-126 / Bloque 5D)

```sql
guia_processing_id IS NOT NULL
```

El lote queda vinculado a la guía de procesamiento que lo generó mediante `guia_processing_id`. El método `_compute_reception_type` asigna `reception_type = 'processed'` a estos lotes.

#### 3.3.1 Matriz de Tipos de Ingesta Operativos y Aplicación de Real Físico ($F3$)

Conforme a las reglas de negocio formalizadas (instrucciones de Cristhian Elgueta y AD-65, AD-79, AD-80, AD-87 y AD-126), la siguiente matriz clasifica **todos los tipos de ingesta operativos documentados en CANON/12** y define dónde aplica el **Volumen Real Físico ($F3$)** con su respectivo estado (`physical_status`):

| Tipo de Ingesta Operativo | Modo / Flujo Documentado | Perfil Canónico | ¿Calcula Real Físico ($F3$)? | `physical_status` | Justificación Operativa y Fórmula |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Guías de Compra / Aserradero** | Modos A y B (Guía con Detalle / Staging, AD-80) | `f1550` / `std` | **SÍ** | `calculado` | Aplica Fórmula F3 ($E_{\text{real}} \times A_{\text{nom}} \times L_{\text{nom}} \times Pz / 10^6$) utilizando el espesor real de la tabla semilla 5A (`lumber.thickness.real.map`). Métrica comparativa `% Dif.Vol` activa. |
| **Recepción por Volumen (Lotes SV)** | Modo C / Flujo Granel (Recepción por Volumen, AD-79 / AD-80) | `granel` / `volume` (AD-79) | **NO** (`0.000`) | `no_aplica` | Ingreso por metros cúbicos globales medidos en camión. No existe desglose pieza a pieza ni escuadría nominal para aplicar F3. Columna `% Dif.Vol` queda vacía. |
| **Consolidación Administrativa** | Modo D / Múltiplos de Tarjas (AD-65 / AD-80) | Consolidación | **SÍ** (cuando aplica) | `calculado` / `no_aplica` | Aplica F3 si la consolidación mantiene escuadría visual homogénea y conteo de piezas. Si agrupa paquetes heterogéneos o sin desglose pieza a pieza, clasifica `no_aplica`. |
| **Procesados o Maquila / Retorno de Servicio** | Imputación SV (Etiqueta $\rightarrow$ SV, AD-87) | `service` (Cepillado / Imputación) | **SÍ** (cuando aplica) | `calculado` / `sin_mapeo` | Si el producto retornado mantiene escuadría visual comercial estándar (ej: 6/4 o 5/4), aplica F3 sobre la escuadría resultante imputada a la tarja SV. Si no cuenta con mapeo, clasifica `sin_mapeo`. |
| **Blanks Directo a Stock** | Flujo 2 / Recepción Directa (AD-65, Regla F6) | `f5085` (Blanks pies) | **NO** (`0.000`) | `no_aplica` | **Regla F6 de Cristhian:** Pasan directo a stock con volumen declarado sin sufrir recálculo ni merma de espesor en Madenat. `vol_physical_real_m3 = 0.000`, `% Dif.Vol` vacía. |
| **Productos Métricos / Perfiles Métricos** | Flujo 1 y 2 (Pino / Eucalipto métrico, AD-80 / AD-112 / AD-127) | `metric` / `standard_madenat` | **NO** (`0.000`) | `no_aplica` | El espesor nominal coincide con el real físico milimétrico ($E_{\text{nom}} = E_{\text{real}}$). No aplica tabla imperial de cuartos, evitando distorsiones volumétricas. |
| **Ingreso Manual / Escuadrías Especiales** | Registro directo manual (AD-80) | Manual | **SÍ** (si mapea) | `calculado` / `sin_mapeo` | Si la escuadría visual existe en la tabla de espesores reales calcula F3; si no existe mapeo clasifica `sin_mapeo` con `% Dif.Vol` vacía sin calcular con ceros. |

### 3.4 Relación con contenedor

Los lotes de guía procesada son seleccionables en wizards de asignación a contenedor (`lumber.container`) cuando cumplen las validaciones operativas del flujo correspondiente.

### 3.5 Impacto en reportes

- La información de OC y proveedor se deriva de `guia_processing_id.order_id` (método `_compute_purchase_info` en `stock_lot.py`).
- `guia_number` muestra `guia_processing_id.name`.
- Reportes que lean únicamente `reception_id` no verán estos lotes.

---

## 4. Flujo 2 — Recepción directa (`lumber_reception`)

### 4.1 Origen funcional

Flujo de ingesta de madera recibida directamente de proveedor, sin procesamiento previo en el sistema. Cubre perfiles Blank, S2S y madera aserrada. El operador carga datos desde Excel/PDF, valida en staging y confirma la creación de lotes vía Gate 3.

### 4.2 Tablas involucradas

| Rol | Modelo | Tabla |
|---|---|---|
| Origen (cabecera) | `lumber.reception` | Cabecera de recepción |
| Origen (líneas) | `lumber.reception.line` | Líneas de staging |
| Destino | `stock.lot` | Lote de inventario |

### 4.3 Campo discriminador

```sql
reception_id IS NOT NULL
```

El lote queda vinculado a la recepción que lo generó mediante `reception_id`. El método `_compute_reception_type` asigna `reception_type = 'raw'` a estos lotes.

### 4.4 Relación con contenedor

Los lotes de recepción directa son seleccionables en wizards de asignación a contenedor cuando cumplen los estados y validaciones del flujo operativo.

### 4.5 Impacto en reportes

- La información de OC y proveedor se deriva de `reception_id.purchase_id` (método `_compute_purchase_info` en `stock_lot.py`).
- `guia_number` muestra `reception_id.name`.
- Reportes que lean únicamente `guia_processing_id` no verán estos lotes.

---

## 5. Regla discriminadora para reportes y consultas

### 5.1 Discriminación explícita

Todo reporte, consolidación o consulta que necesite separar lotes por origen debe usar **siempre** uno de estos dos filtros, nunca `guia_number` ni joins sin discriminador:

| Flujo | Filtro SQL/ORM |
|---|---|
| Guía procesada | `guia_processing_id IS NOT NULL` |
| Recepción directa | `reception_id IS NOT NULL` |

### 5.2 Prohibiciones

- **No usar `guia_number` como discriminador.** `guia_number` es un campo informativo/computado y no es confiable para distinguir origen.
- **No usar `lumber_reception_id` como discriminador.** Es un campo legacy/huérfano no utilizado por la lógica operativa actual. El campo canónico es `reception_id`.
- **No hacer joins ciegos.** Un JOIN sobre `reception_id` sin verificar nulos puede excluir lotes de guía procesada. Un JOIN sobre `guia_processing_id` sin verificar puede excluir lotes de recepción directa.
- **No asumir que todos los lotes tienen `reception_id`.** Los lotes de guía procesada no lo tienen.
- **No asumir que todos los lotes tienen `guia_processing_id`.** Los lotes de recepción directa no lo tienen.

### 5.3 Consolidación de ambos flujos

Cuando un reporte requiera consolidar lotes de ambos orígenes, debe:

1. Identificar explícitamente el origen en cada fila.
2. Usar `LEFT JOIN` o `COALESCE` para campos que solo existen en un flujo.
3. Incluir columna de origen (`reception_type`) en el resultado.

El módulo `lumber_container` ya opera bajo este principio: agrupa lotes de ambos flujos sin mezclar su trazabilidad de origen.

---

## 6. Hallazgos de sesión 2026-06-16

### 6.1 Lotes de guía procesada (flujo 1)

- **19 lotes** con `guia_processing_id = 14` vinculados a la guía `19846`.
- Estos lotes son correctos en su flujo. No deben forzarse a recepción directa.

### 6.2 Lotes de recepción directa con guía coincidente (flujo 2)

- **26 lotes** de recepción directa con `guia_number` coincidente con recepciones existentes.
- La coincidencia por `guia_number` es un hallazgo operativo, pero no constituye el discriminador canónico.
- El discriminador correcto es `reception_id` cuando está poblado.

### 6.3 Inconsistencias en `reception_id`

- Existen lotes de recepción directa cuyo `reception_id` no está poblado.
- **Causa probable:** el flujo de recepción no está escribiendo la FK `reception_id` al crear lotes durante Gate 3.
- **Impacto:** estos lotes no pueden rastrearse de forma canónica hasta su recepción de origen.

### 6.4 Convergencia en `lumber_container`

- `lumber_container` agrupa lotes de ambos flujos correctamente.
- La convergencia en contenedores es funcionalmente correcta.
- No se requiere modificar este comportamiento en esta fase.

### 6.5 Aclaración sobre `lumber_reception_id`

- El campo `lumber_reception_id` existe en el modelo `stock.lot` pero no forma parte del flujo operativo canónico auditado.
- Ningún método activo (`_compute_reception_type`, `_check_reception_guia_exclusivity`, `_compute_guia_number`, `_compute_purchase_info`) lo referencia como discriminador.
- La auditoría confirma que el campo operativo real es `reception_id`. `lumber_reception_id` se considera un remanente histórico sin rol operativo actual.

---

## 7. Fix de datos documentado

### 7.1 Lotes vinculables por coincidencia operativa

Los lotes de recepción directa con guía coincidente pueden verificarse con consultas puntuales, pero la coincidencia de guía no debe usarse como discriminador documental.

Si se requiere una verificación puntual:

```sql
SELECT id, name, reception_id, guia_number
FROM stock_lot
WHERE reception_id IS NOT NULL
  AND guia_number IN (SELECT name FROM lumber_reception);
```

### 7.2 Lotes de guía procesada

Los 19 lotes con `guia_processing_id = 14` y guía `19846` son correctos. **No forzar** `reception_id` en estos lotes. Pertenecen al flujo de guía procesada.

---

## 8. Fix de flujo pendiente

### 8.1 `lumber_reception` no puebla `reception_id` consistentemente

**Hallazgo:** Existen lotes creados desde recepción directa sin `reception_id` poblado.

**Línea de investigación requerida:**
- Revisar el método que crea `stock.lot` durante Gate 3 en `lumber_reception`.
- Verificar si la asignación de `reception_id` está condicionada a algún flag, estado o rama de lógica.
- Determinar si es un bug sistemático o un caso aislado por flujo interrumpido.
- Confirmar la trazabilidad operativa real a través de `reception_id`, no de `lumber_reception_id`.

**No aplicar scripts destructivos ni updates masivos sin diagnóstico confirmado.**

---

## 9. Estado y seguimiento

### 9.1 Estado actual

| Ítem | Estado |
|---|---|
| Documento canónico de flujos de ingesta | ✅ CREADO (2026-06-16), CORREGIDO (2026-06-16) |
| Regla discriminadora documentada | ✅ Vigente — `reception_id` / `guia_processing_id` |
| Constraint de exclusividad en código | ✅ Activa |
| `reception_id` no poblado en algunos lotes | 🔴 Pendiente de diagnóstico |
| `lumber_reception_id` como campo legacy | 🏷️ Catalogado como huérfano — no usar en nuevos desarrollos |
| Convergencia en `lumber_container` | ✅ Funcional |
| Migración picking layer `lumber_reception_id` → `reception_id` | ✅ COMPLETADA (2026-06-16) — ver sección 10 |

### 9.2 Próximos pasos

1. Diagnosticar por qué `lumber_reception` no puebla `reception_id` en todos los lotes creados.
2. Verificar que todos los reportes activos usen el discriminador explícito (`reception_id` / `guia_processing_id`).
3. Agregar validación en Gate 3 que rechace la creación de lotes sin FK de origen poblada.
4. Evaluar si corresponde eliminar o marcar como deprecated el campo `lumber_reception_id` en una fase futura (puede hacerse en ambas tablas: `stock.lot` y `stock.picking`).

### 9.3 Dependencias

- `stock_lot.py` (`StockLotExtended`) — modelo base, constraint y campos discriminadores.
- `lumber_reception.py` — creación de lotes en Gate 3.
- `madenat_guia_processing.py` — creación de lotes desde guía procesada.
- `reception_service.py` — servicio de escritura a stock.
- `stock_picking.py` — capa de picking con `reception_id` como campo canónico.

### 9.4 Responsable de actualización

Arquitecto / Tech Lead. Este documento debe actualizarse si:
- Se modifica la constraint de exclusividad.
- Se agrega un tercer flujo de ingesta.
- Se resuelve el diagnóstico de `reception_id` no poblado.
- Cambia la semántica de `reception_type` o los estados operativos que afectan la selección en contenedores.
- Se elimina o migra el campo legacy `lumber_reception_id`.

---

## 10. Migración picking layer — `lumber_reception_id` → `reception_id`

### 10.1 Contexto

Hasta el 2026-06-16, el modelo `stock.picking` usaba `lumber_reception_id` como campo almacenado que funcionaba como FK operativa hacia `lumber.reception`. Este campo era el ancla de navegación (`action_open_lumber_lots`), métricas agregadas (`_compute_reception_totals`, `_compute_validation_status`) y búsqueda en vistas. Simultáneamente, el mismo `stock.picking` se creaba mediante writes explícitos a `lumber_reception_id` en tres puntos:

- `lumber_reception.py:_create_stock_picking` → `lumber_reception_id: self.id`
- `reception_service.py:create_stock_picking` → `lumber_reception_id: reception.id`
- `stock_picking.py:create_from_lumber_reception` → `picking_vals['lumber_reception_id'] = reception_id`

Esto creaba una dualidad operativa: el flujo canónico de lotes se anclaba en `reception_id` (en `stock.lot`), pero la capa de picking persistía en `lumber_reception_id`. La política documental ya había establecido `reception_id` como el campo canónico operativo.

### 10.2 Cambios aplicados

#### 10.2.1 `stock_picking.py` — campos

| Antes | Después |
|---|---|
| `lumber_reception_id` = `fields.Many2one` almacenado (readonly=True) | `reception_id` = `fields.Many2one` almacenado (index=True) |
| — | `lumber_reception_id` = `fields.Many2one(related='reception_id')` — legacy, solo lectura |
| `lumber_lot_ids` related a `lumber_reception_id.lot_ids` | `lumber_lot_ids` related a `reception_id.lot_ids` |
| `action_open_lumber_lots` usa `self.lumber_reception_id.id` | `action_open_lumber_lots` usa `self.reception_id.id` |
| `create_from_lumber_reception` escribe `lumber_reception_id` | `create_from_lumber_reception` escribe `reception_id` |

#### 10.2.2 `lumber_reception.py` y `reception_service.py` — writes

| Punto | Antes | Después |
|---|---|---|
| `lumber_reception.py:_create_stock_picking` (línea ~2049) | `lumber_reception_id: self.id` | `reception_id: self.id` |
| `reception_service.py:create_stock_picking` (línea ~117) | `lumber_reception_id: reception.id` | `reception_id: reception.id` |

#### 10.2.3 Vistas (`stock_picking_views.xml`)

| Vista | Antes | Después |
|---|---|---|
| Tree | `<field name="lumber_reception_id"/>` | `<field name="reception_id"/>` |
| Search: filter_domain | `('lumber_reception_id', 'ilike', self)` | `('reception_id.name', 'ilike', self)` |

#### 10.2.4 Migración de datos (`18.0.5.2.0/post-migrate.py`)

Script idempotente que copia `lumber_reception_id → reception_id` en `stock_picking` para preservar trazabilidad histórica antes de que Odoo reconvierta la columna antigua.

### 10.3 Estado resultante

- **`reception_id`** es el campo canónico operativo en `stock.picking`. Todos los writes y lecturas operativas lo usan directamente.
- **`lumber_reception_id`** en `stock.picking` es ahora un campo `related` a `reception_id`. Persiste en la UI como etiqueta de compatibilidad, pero no acepta escritura directa ni participa en flujos de creación.
- El flujo de lotes (`stock.lot`) no fue modificado. Sigue usando `reception_id` como FK canónica.
- La trazabilidad histórica se preserva mediante el script de migración que copia los valores antes de la reconversión de columna.

### 10.4 Archivos modificados

| Archivo | Tipo de cambio |
|---|---|
| `madenat_lumber_core/__manifest__.py` | Versión 18.0.5.1.0 → 18.0.5.2.0 |
| `madenat_lumber_core/models/stock_picking.py` | Campos: `reception_id` almacenado + `lumber_reception_id` relacionado; referencias internas |
| `madenat_lumber_core/models/lumber_reception.py` | Write canónico en `_create_stock_picking` |
| `madenat_lumber_core/models/reception_service.py` | Write canónico en `create_stock_picking` |
| `madenat_lumber_core/views/stock_picking_views.xml` | Tree y search → `reception_id` |
| `madenat_lumber_core/migrations/18.0.5.2.0/post-migrate.py` | Script de migración de datos |
| `madenat_lumber_docs/CANON/12_FLUJOS_INGESTA.md` | Documentación actualizada (este documento) |

### 10.5 Verificación

- Ningún write operativo escribe `lumber_reception_id` en `stock.picking`.
- La UI de picking sigue mostrando la guía Madenat (vía `reception_id` que es el campo almacenado real).
- La búsqueda por guía funciona correctamente (vía `reception_id.name`).
- La migración de datos preserva los valores históricos.
- El flujo de lotes (`stock.lot` → `reception_id`) permanece intacto.

---

*Documento creado: 2026-06-16 — Sesión de auditoría documental canónica.*  
*Versión: 1.3.0 — Agregada sección 10 (migración picking layer `lumber_reception_id` → `reception_id`) y sección 11 (consolidación administrativa como tercera vía complementaria, AD-65).*

---

## 11. Consolidación administrativa — tercera vía de resolución de origen (AD-65, diseño aprobado)

### 11.1 Naturaleza

La **consolidación administrativa** (AD-65, pendiente de implementación) es una vía de **resolución de origen a nivel administrativo** para la recepción a granel: el operador puede, manual y opcionalmente, asignar/consolidar el saldo de una guía de procesado contra una o más guías de origen enviadas a proceso. Funciona incluso sin guías de origen candidatas.

### 11.2 Relación con los discriminadores canónicos

Esta vía **no reemplaza** los discriminadores `reception_id` / `guia_processing_id` de las secciones 2–5; **los complementa**. Los discriminadores siguen siendo la fuente de verdad de origen de cada `stock.lot`; la consolidación administrativa es una relación de **saldo agregado (Mass Balance)** entre guías de origen y de retorno, sin vínculo lote a lote (coherente con DEC-002).

### 11.3 Regla normativa (textual, AD-65 §1.7)

> El sistema no debe validar, exigir, ni asumir correspondencia de detalle (volumen, piezas, paquetes) entre lo enviado a proceso y lo retornado procesado. La relación es de balance agregado administrativo (Mass Balance), nunca de igualdad ni de correspondencia física o numérica exacta.

### 11.4 Nota de mantenimiento

Se cumple el criterio de §9.4 ("se agrega un tercer flujo de ingesta"): esta sección aclara que la consolidación es **administrativa y complementaria**, no un tercer flujo de creación de `stock.lot`.

### 11.5 Volumen oficial de una Recepción por Volumen (2026-09-26, AD-79)

Regla funcional vigente, verificada en `madenat_lumber_intake/models/intake_guia_processing.py`
(`OFFICIAL_VOLUME_SOURCES` y `_compute_official_volume_m3`):

| Prioridad | Campo | Origen documental |
|---|---|---|
| 1 | `volume_pdf_m3` | Guía PDF |
| 2 | `volume_excel_m3` | Packing Excel |
| 3 | `packing_volume_declared_m3` | Packing declarado |

- Se toma el **primer valor estrictamente positivo** de la lista.
- Si ninguna fuente es positiva, **no existe volumen oficial** para el ingreso.

**Distinción profesional de fuentes:**

- **Volumen oficial:** dato documental que gobierna el flujo (referencia de contraste para stock, conciliación y consolidación). Expuesto como `official_volume_m3` con su origen en `official_volume_source`.
- **Total de líneas PDF (`volume_detail_m3`, suma del detalle):** evidencia de control documental interno; su diferencia contra el volumen oficial es *warning* documental, no bloqueante, y **nunca** reemplaza el volumen oficial.
- **Volumen operativo (`volume_operational_m3`):** referencia operativa editable por el operador (AD-76); **nunca** sustituye al volumen oficial ni lo sobrescribe.

**No son fallbacks del volumen oficial:** `volume_detail_m3` y la suma de líneas PDF, `volume_operational_m3`, `volumen_declarado_m3`, `vol_comercial_pdf`, `vol_comercial`, `vol_fisico`, `vol_total_m3`, ni valores derivados de stock, conciliación o costeo.

**Bloqueo operativo:** la rama de Volumen de `action_validate` (F3.1) exige volumen documental oficial disponible (`intake_guia_processing.py:415`, `intake_console.py:1112`); sin fuente positiva el sistema responde:

```text
No existe volumen documental oficial para enviar a stock.
```

**Alcance:** el volumen oficial es la fuente declarada del futuro contexto de la Etiqueta SV
documentada en `00_ARQUITECTURA.md` §4.8. Los valores históricos de casos concretos **no** forman
parte de esta regla general: se documentan únicamente como caso histórico preservado en
`04_DECISION_LOG.md` (AD-79) y `02_CONTINUIDAD.md` §14.3, y no se modifican.

### 11.6 Alcance del gate dimensional del core en flujos de Volumen (2026-09-26, cierre T2)

El gate dimensional de espesor nominal de `madenat.guia.processing` (`action_validate`,
`action_process_from_staging`) aplica **solo a flujos dimensionales** (`tipo_recepcion` distinto de `granel`).
Una Recepción por Volumen se gobierna con el volumen oficial documental (§11.5) y **no inventa** espesor
nominal: la línea de resumen (`_create_granel_summary_line`) y las líneas de detalle de Volumen
(`_create_granel_detail_lines`) conservan `espesor_nominal_mm = 0.0` y su volumen documental.

En el runtime desplegado (con `madenat_lumber_intake` instalado), la rama de Volumen de `action_validate` es la
que valida el envío a stock y exige volumen oficial positivo; el gate dimensional del core solo es alcanzable
en un registro core (sin Intake) o en guías `compra`/`service`. Verificado en la sesión de cierre T1–T6
(`05_BACKLOG.md`, `03_TESTS.md` §9.7).

### 11.7 Fase 2 — Volumen oficial, bloque SV visible y ciclo de vida de guías (2026-09-28, AD-80)

**Jerarquía de volumen (Consola, `ingestion_type = 'volume'`).**

```text
VOLUMEN OFICIAL DE LA GUÍA            ← único volumen primario
<official_volume_m3> m³   Fuente: <official_volume_source>
Gobierna stock, conciliación y consolidación.

M³ declarado por Operaciones (referencia)
No gobierna stock ni reemplaza el volumen oficial.
Volumen operativo de referencia (no gobierna stock)

Control documental interno (auditoría)     ← solo si hay diferencia real
Total de líneas del detalle PDF (control interno)
Diferencia vs volumen oficial
```

El encabezado no muestra el agregado competidor `Volumen:` para Volumen.

**Bloque `ETIQUETA SV Y SALDO OPERATIVO` (solo lectura).** Visible solo con lote SV real
(`declared_sv_lot_id`); sin lote muestra `Se asignará al enviar a stock.` y ningún botón de
mutación. Expone etiqueta SV, volumen documental original, volumen regularizado, volumen
rebajado, saldo disponible, piezas disponibles (solo con `sv_pieces_enabled`) y advertencia
documental (solo si existe), más las cinco acciones SV autorizadas (modificar etiqueta,
regularizar volumen, rebajar etiqueta, reversar rebaja y ver historial). Todas delegan en los
wizards y en el ledger del Programa SV; la Consola nunca escribe `stock.lot.name`, volumen ni
saldo.

**Ciclo de vida controlado (Modos A–D).** Diagnóstico único de trazas (lotes, pickings,
movimientos, líneas de movimiento, quants, operaciones SV, costo, valoración, consolidación,
factura, contenedor, embarque y período cerrado) y ejecución en cuatro modos documentados en
`04_DECISION_LOG.md` (AD-80):

| Modo | Efecto | Evidencia |
|---|---|---|
| A. Eliminar definitivamente | `unlink()` canónico solo sin ninguna traza | `guia_delete_permanent` |
| B. Cancelar y conservar | `action_force_cancel()` sin cambios de semántica | Chatter del origen |
| C. Purgar de forma controlada | operaciones SV en borrador → lote técnico → guía; exige `PURGAR` y Jefatura de Operaciones | `guia_purged` |
| D. Bloquear y escalar | no elimina nada; lista de bloqueadores y rutas correctas | `guia_delete_blocked` |

Los eventos se registran en `madenat.audit.log` con snapshot y firma SHA-256
(`action_type` extendido con `guia_delete_blocked`, `guia_delete_permanent` y `guia_purged`).

**Evidencia documental.** Los Modos A y C se bloquean además cuando la guía tiene evidencia:
adjuntos (`ir.attachment`, incluidos los documentos PDF/Excel), mensajes de chatter con
contenido o referencias genéricas persistentes por `(res_model, res_id)` (`mail.activity`,
`product.document`, `quotation.document`, …). Odoo **destruye** el chatter y los adjuntos al
eliminar el registro, de modo que la eliminación no puede dejar evidencia huérfana ni
intrazable: se bloquea y la ruta correcta es el Modo B (cancelar conservando trazabilidad). El
aviso automático de creación de `mail.thread` y el estado transitorio de UI no cuentan como
evidencia. El snapshot de auditoría del Modo D incluye el inventario de evidencia detectada.

### 11.8 Imputación SV (etiqueta→SV) — vía oficial del retorno procesado (2026-10-01, AD-87)

**Naturaleza.** Para la **compra de volumen (SV)**, el vínculo entre el volumen comprado y la **madera procesada que retorna** del procesador no es una relación de detalle ni de genealogía física: es una **imputación declarada** por **etiqueta** con su **volumen NOMINAL editable**, contra **uno o varios SV** (decisiones D2/D3). Norma completa: `19_IMPUTACION_SV_Y_PROCESADORES.md`.

**Reglas que afectan este documento.**
- **El SV nunca se exporta.** Los lotes `lot_flow_type='volume'` **no** participan de la consolidación/rebaja de **exportación** (documento `18`), que opera sobre lotes de **tarja**. La **salida nativa del quant del SV** ocurre en la **imputación** (ledger `madenat.sv.operation` tipo `imputacion`), no en la rebaja de contenedor (AD-82 se alinea; AD-83 queda **reemplazada** por AD-87).
- **El retorno es stock nuevo e independiente** (§11.2/§11.3; AD-65 §1.6; DEC-002). La imputación **no** crea genealogía; `parent_lot_id` pasa a **opcional** en un paso futuro controlado (D10).
- **Volumen oficial (§11.5) sigue siendo la fuente del SV**; la imputación **no** reemplaza el volumen oficial y el volumen nominal de la etiqueta es editable.
- **Saldo por procesador:** el SV enviado al procesador vive en una ubicación **interna** `Procesadores/<X>` (inventario de MADENAT, D5); su saldo restante se controla por reporte.

**Referencias cruzadas.** `17` §2.8 (nota SV, reescrita); `18` §7 (pantallas, SV fuera de exportación); `04` AD-87/AD-88; `05_BACKLOG` (fases I1–I6).

---

### 11.9 Identificación de retorno de servicio (no bloqueante) — 2026-10-07

**Naturaleza.** La **Guía de procesado** (`madenat.guia.processing`) registra si el ingreso
Procesado de servicio **es un retorno de servicio** mediante `service_return_confirmation`
(Selection de **tres estados**):

| Valor | Significado |
|---|---|
| *vacío* | **pendiente de identificación** (NO equivale a «No») |
| `yes` | es retorno de servicio |
| `no` | no es retorno de servicio |

**Reglas.**
- **No bloqueante.** La identificación **no** impide la ingesta ni el envío a stock por sí sola;
  no altera `tipo_recepcion`, stock ni costes; no dispara imputaciones. El vacío es un estado
  válido y se completa posteriormente según permisos y reglas vigentes. **No** se debilitan las
  demás validaciones (permisos, dimensiones, producto, tipo de cambio, trazabilidad,
  anti-duplicado).
- **Alcance:** ingreso Procesado de servicio (`tipo_recepcion == 'service'`). Excluye `compra`,
  `granel` (Volúmenes) y Producto.
- **Persistencia** en la Guía. La Consola de Ingreso de Madera (vista SQL de solo lectura) la
  expone por **proxy no almacenado** (compute + inverse) **editable** por Operaciones, sin
  duplicar el dato.
- **Relación con I2.** La identificación **precede** e identifica el retorno; **no** sustituye ni
  dispara la imputación SV (I2, §11.8; CANON/19 §19.9). «Imputación posterior» es un acto
  **declarativo e independiente**.
- **Regla con imputaciones aplicadas.** Si la guía tiene **imputaciones SV `applied`**, no se
  permite cambiar la identificación a «No» ni vaciarla; la corrección exige **reversar** primero
  las imputaciones (mecanismo existente). No se eliminan relaciones en silencio.
- **Filtros** en la búsqueda de la guía: «Retornos de servicio» / «No retornos de servicio» /
  «Retorno de servicio sin confirmar». El filtro **«Retornos sin imputación aplicada»** (Logística)
  detecta **ausencia de imputación `applied`** y **NO evalúa cobertura parcial** (limitación).

**Estado.** Implementado y probado en **copia de trabajo aislada**
(`IMPL_SERVICE_RETURN_AB_20261007/`); **NO aplicado** al entorno activo. Detalle en
`04_DECISION_LOG.md` **AD-102**.

---

## 12. Reglas Operativas de Ingreso Directo, Blanks y Patios (AD-116 / AD-117)

> Alineación con las especificaciones de Operaciones (Cristhian Elgueta, 2026-10-17 / AD-116 y AD-117).

### 12.1 Flujo Directo de Blanks Clear (F4/F6)
- **Ingreso sin recálculo:** Los paquetes de Blanks pasan directo a stock físico y documental cuando se envían; si el registro posee volumen documental declarado (`vol_documental_m3 > 0`), este valor se conserva intacto en `vol_shipment_m3` y `vol_purchase_m3`, sin ejecución de recálculos dimensionales.
- **Fórmula F4 limpia:** Cuando aplica el cálculo de exportación en pies, no se descuenta $1/16"$ al espesor ($6/4 = 1,5"$ nominal limpio), aplicando $(1,5 \times (\text{Ancho} + 0,125") \times \text{Largo}_{ft} \times \text{Piezas}) / 5085,312$.
- **Identidad de producto y certificación de secado:** Los Blanks se describen documentalmente como **"Madera Aserrada Seca"**, almacenando en `stock.lot` los parámetros de secado en horno (`drying_temp_c`, `drying_duration_hours`, `drying_date`), validados dinámicamente según la configuración de la empresa.

### 12.2 Política de Patios Operativos y Consola de Recepción (F7)
- **Patios como Ubicaciones de Inventario:** Los patios son ubicaciones internas de stock (`stock.location`) identificadas mediante el marcador booleano `is_patio = True`:
  - Creables y editables por Operaciones desde el menú *MADENAT Lumber > Configuración > Patios de Recepción*.
  - Desacoplados de cualquier ID hardcodeado (H2): no existen parámetros fijos de ubicación en código ni acoplamiento forzado con el procesador (ID 676).
- **Consola de Recepción:** Las vistas de lista y búsqueda de `lumber.reception` incorporan:
  - Selector de Patio restringido a ubicaciones con `is_patio = True`.
  - Filtros directos: "Con Patio Asignado", "Sin Patio Asignado" y "Con Orden de Compra".
  - Agrupadores por Patio (`location_id`) y por Orden de Compra (`purchase_order`).

### 12.3 Señal Explícita `is_s2s_inches` y Orden Canónico de Resolución de Ancho (AD-118)
- **Eliminación de heurística numérica:** Se suprime la comparación de punto flotante con tolerancia (`abs(s2s_in - w_in) < 0.01`) de `get_s2s_adjustment()`.
- **Señal explícita en normalización:** En documentos de proveedores como JCE (`NVTA881333` / `GDE 95806`) donde la notación combinada expresa dimensiones comerciales en pulgadas (ej. `5/4x5.3/8x16`), el normalizador documental (`_validar_y_enriquecer_lineas()`) detecta la presencia de ancho en pulgadas comerciales, normaliza a milímetros en staging ($5,375 \times 25,4 = 136,525\text{ mm}$) y emite la señal explícita `is_s2s_inches=True`.
- **Orden canónico de resolución de ancho:**
  1. **Rama 1 — Manual (`export_width_manual_inches`):** Si el operador asignó un valor manual mayor a cero con motivo obligatorio, prevalece sobre cualquier cálculo (`madenat_guia_processing_line.py:270` y `stock_lot.py:90`).
  2. **Rama 2 — Tabla S2S activa:** Si `rough_mm` existe en el modelo `lumber.width.s2s.map` con `active=True`, se asigna el ancho S2S mapeado más el sobreancho (`madenat.s2s_overwidth_inches`, por defecto $0,125"$) (`madenat_ingestion_config.py:160-165`).
  3. **Rama 3 — Documental en pulgadas S2S (`is_s2s_inches=True`):** Si la señal viene activa desde el parser, se reconoce que el ancho documental ya representa la escuadría S2S, retornando exactamente el sobreancho sin duplicar la base (`utils_uom.py:95`), logrando el volumen documental exacto de $4,997\text{ m}^3$ para 231 piezas de 16 ft en JCE (`madenat_ingestion_config.py:167-170`).
  4. **Rama 4 — Directo métrico:** Si el ancho no existe en tabla y no es documental S2S (`madenat_ingestion_config.py:172-203`):
     - Si $\text{rough\_mm} < \text{madenat.direct_width_min_mm}$ ($170\text{ mm}$): aplica la política `madenat.out_of_table_behavior` (`'warning'` emite advertencia en logs y chatter de guía aplicando $\text{mm} / 25,4$; `'block'` interrumpe con `ValidationError`; `'direct'` aplica $\text{mm} / 25,4$ sin advertencia).
     - Si $\text{rough\_mm} \ge \text{madenat.direct_width_min_mm}$ ($170\text{ mm}$): aplica conversión métrica directa $\text{mm} / 25,4$ sin advertencia. Para el caso especial de $150\text{ mm}$, por encontrarse en la tabla S2S activa, toma siempre la Rama 2 ($5\text{ }5/8" + 1/8" = 5,750"$).

### 12.4 Cierre Técnico Previo al Despliegue (AD-119)
- **Tabla S2S sin copia en código (F1):** Se elimina el diccionario estático de respaldo de `madenat_ingestion_config.py`. El modelo `lumber.width.s2s.map` es la fuente única de verdad. Si la tabla no contiene registros activos, se interrumpe la ejecución levantando `UserError` con log estructurado `[MADENAT-S2S-EMPTY]`. La entrada de 115 mm en base de datos mapea canónicamente a $4\text{ }3/8" = 4,375"$ (resultando en $4,500"$ con sobreancho = $1,742\text{ m}^3$ en 100 piezas).
- **Retiro de deduction_factor del modelo (F2):** Se elimina el campo `deduction_factor` de `lumber.export.formula` y de las vistas XML sin alterar las columnas ni filas en la base de datos PostgreSQL, garantizando la preservación estricta de datos históricos.
- **Constante única 1550.003 (F3):** Se unifica en `utils_uom.py` la constante a `Decimal('1550.003')` con alias `INCH_SQ_METERS_TO_M3 = CONST_M3_TO_IN2_M`, demostrándose matemáticamente impacto cero ($0,000\text{ m}^3$) en todos los volúmenes del sistema.
- **Script de comprobación pre-deploy (F7):** Script de solo lectura en `madenat_lumber_core/scripts/pre_deploy_health_check.py` para validar 15 anchos, parámetros y perfiles antes y después de cualquier despliegue.

### 12.5 Cierre Técnico Final y Gobernanza de Anchos S2S (AD-120)
- **Ámbito del UserError por tabla S2S vacía (G5):** El error de interrupción `UserError` se limita estrictamente a las ramas que dependen de la tabla S2S (perfiles imperiales $f1550$ / $f5085$ con ancho rough $< 170\text{ mm}$). Los perfiles métricos y anchos directos ($\ge 170\text{ mm}$) o con señal explícita documental (`is_s2s_inches=True`) no dependen de la tabla S2S y no se bloquean aunque la tabla se encuentre vacía.
- **Edición por interfaz con trazabilidad y coherencia (G8 / D6):** El modelo `lumber.width.s2s.map` habilita trazabilidad completa en chatter (`mail.thread`) para auditoría de modificaciones (usuario, fecha y valores anteriores). Se implementa constraint de coherencia `_check_decimal_label_coherence` que impide divergencias entre la etiqueta fraccionaria y el decimal almacenado dentro de una tolerancia de $\pm 1/16"$ ($0,0625$).
- **Invarianza de registros históricos (R5/D6):** Editar un registro en `lumber.width.s2s.map` solo afecta cálculos NUEVOS; no recalcula registros históricos almacenados en `madenat_guia_processing_line` ni `stock_lot`. Para deshabilitar un ancho se utiliza el archivado (`active=False`) preservando la historia.

### 12.6 Matriz de Tipos de Ingesta por Regla de Cálculo de Volumen Real Físico F3 (AD-126 / Bloque 5B)

Tras la armonización canónica con las directrices de Cristhian Elgueta y la arquitectura de ingesta (AD-65, AD-79, AD-80, AD-87 y AD-126), la siguiente matriz define formalmente qué tipos de ingesta y perfiles calculan el **Volumen Real Físico ($F3$)** frente a $F1$ (Compra / Nominal) y $F2$ (Exportación / Embarque):

| Tipo de Ingesta / Flujo | Perfil Canónico | ¿Calcula F3 (Real Físico)? | Fórmula Aplicada / Justificación Operativa |
| :--- | :--- | :---: | :--- |
| **Compra Aserradero (Producto)** | `f1550` (Imperial estándar) | **SÍ** | $\text{Espesor Real (mm de 5A)} \times \text{Ancho Nominal (mm)} \times \text{Largo (m)} \times \text{Piezas} / 1.000.000$. Requiere escuadría visual mapeada en `lumber.thickness.real.map`. |
| **Blanks Directo a Stock** | `f5085` (Blanks en pies) | **NO** (`0.000`) | **Regla F6 (Cristhian):** Pasan directo a stock con el volumen declarado sin recálculos. No sufren cepillado S2S ni merma de espesor físico en Madenat. `vol_physical_real_m3 = 0.0`. |
| **Métrico / Perfiles Métricos** | `metric` (Pino / Eucalipto) | **NO** (`0.000`) | En perfiles puramente métricos, el espesor de compra coincide con la dimensión física nominal. No aplica tabla imperial 5A salvo que exista escuadría comercial en cuartos. |
| **Recepción por Volumen (Lotes SV)** | `granel` / `volume` (AD-79) | **NO** (`0.000`) | Ingreso por metros cúbicos globales medidos en camión (báscula/metro cúbico). No posee desglose pieza a pieza ni escuadría nominal. |
| **Retorno de Servicio / Procesado** | `service` (Cepillado / Imputación) | **SÍ** (cuando aplica) | Si el producto retornado mantiene escuadría visual comercial estándar (ej: 6/4), aplica F3 sobre la escuadría resultante imputada a la etiqueta SV (AD-87). |
| **Blanks con Largo Métrico** | `f1550` / `metric` mixto | **SÍ** (si no es directo a stock) | Aplica F3 si se trata de madera aserrada estándar con largo métrico y espesor nominal visual mapeable. |

### 12.7 Flujo de Edición de Dimensiones Antes y Después del Envío a Stock (AD-132 / Bloque H5)

- **Antes del envío (Fase de Staging en Intake):**
  - **Modelos operativos:** `madenat.guia.processing.line` y `lumber.reception.line`.
  - **Recálculo integral de compra y exportación:** La edición manual del ancho nominal (`ancho_nominal_mm` o `width_nominal`) recalcula inmediatamente tanto el volumen de compra (`vol_purchase_m3`) como el volumen de exportación (`vol_shipment_m3`) a través de la API única `resolve_export_width_details(rough_mm=effective_w)` donde `effective_w = ancho_nominal_mm or ancho_mm`.
  - **Estado fuera de tabla y override manual:** Se evalúan uniformemente sobre el ancho efectivo resuelto. Si el ancho nominal es vacío o 0, respalda en `ancho_mm`. El override manual (`export_width_manual_inches`) mantiene su precedencia canónica absoluta.
  - **Blanks inalterados:** Para subproductos de la familia `blank`, se preserva estrictamente la regla de oro: compra = exportación (sin alteración de volumen).

- **Después del envío (Fase de Stock en Lote):**
  - **Modelo operativo:** `stock.lot`.
  - **Salvaguarda de staging estricta:** Para lotes que provienen de recepción o proceso (`reception_id`) con volumen mayor a 0,001 m³, el volumen de exportación e inventario permanece protegido e inmutable (no se recalcula automáticamente).
  - **Aviso de auditoría en chatter:** Al modificar piezas o ancho (`piezas`, `ancho_mm`, `ancho_nominal_mm`), el sistema registra automáticamente un mensaje en el chatter del lote: `"dimensiones modificadas después del ingreso; el volumen no se recalculó"`.
  - **Escalado de volumen en rebaja:** La lógica de recálculo proporcional de volumen ante rebajas físicas de piezas queda formalmente implementada en el **Bloque 7** mediante la extinción del quant nominal completo y reconocimiento de `rebaja_merma_m3` (AD-133).

### 12.8 Asistente de Importación de Consolidación de Tarjas desde Excel (AD-133 / Bloque 7.2)

- **Modelo Operativo:** `lumber.consolidation.import.wizard` y líneas pendientes `lumber.consolidation.import.pending` en `madenat_lumber_logistics`.
- **Estructura Doble Bloque:** Soporte nativo para lectura de planillas de consolidación en formato real exportador:
  - **Bloque Izquierdo (Exportación):** Columnas 1 a 13 (Embarcador, Producto, Planta, Etiqueta, Pqts, Subproducto, Espesor, Ancho, Largo, Piezas, M3, Guía, Fecha).
  - **Bloque Derecho (Compra Nominal):** Columnas 15 a 27 (mismas especificaciones en base nominal de compra).
- **Manejo de Filas sin Etiqueta:**
  - Filas que carecen de etiqueta o cuyo proveedor no coincide unívocamente no se descartan ni interrumpen la importación.
  - Se capturan como registros de asignación pendiente en `lumber.consolidation.import.pending`, preservando proveedor, piezas y volúmenes para conciliación manual en UI.
- **Validación y Detección de Discrepancias:**
  - Compara los volúmenes declarados en la planilla contra los volúmenes registrados en el sistema (`vol_shipment_m3` y `volume_purchase_m3`).
  - Emite informe detallado de diferencias tolerando $\pm 0,001\text{ m}^3$ por redondeo.
- **Garantía de Invarianza Estructural:**
  - El asistente opera como herramienta de auditoría y consolidación; **no crea lotes ni modifica inventario en BD**, garantizando el principio de inmutabilidad de datos almacenados.




---

## 13. Procedencia del perfil de lectura y vigencia de la lectura (AD-134 / FASE 13-2D, 2026-10-26)

### 13.1 Secuencia canónica del ingreso (sin cambios de pantallas)

```
Adjuntar documentos → «Leer documento» (state = previewed + reading_signature)
                    → «Continuar ingreso» (guardas → _route_granel/_route_producto/_route_procesado)
```

- La lectura deja el wizard en **`previewed`** en las tres modalidades (Producto, Procesado y Volúmenes).
- La derivación se bloquea si falta la lectura (`state != 'previewed'`) o si la huella no coincide con los
  datos actuales (lectura rancia).

### 13.2 Procedencia del perfil

| `profile_origin` | Significado | Efecto de la sugerencia documental |
|---|---|---|
| `default` | Valor inicial del campo (sin análisis) | Aplica el perfil sugerido y pasa a `suggested` |
| `suggested` | Fijado por la sugerencia documental | Puede actualizarse con una nueva sugerencia |
| `chosen` | Elección explícita del operador | **No** se aplica; sólo se registra en `profile_suggested` y se muestra el aviso |

`profile_mismatch_hint` (no bloqueante) aparece cuando `profile_origin = 'chosen'`, existe
`profile_suggested` y el perfil aplicado difiere de la sugerencia. La lectura se hace **siempre** con la
elección del operador.

### 13.3 Invalidación de la lectura

Entradas vigiladas (`_READING_INPUT_FIELDS`): `intake_modality`, `ingestion_profile`,
`assignment_location_id`, `tipo_detalle_granel`, `excel_file`, `excel_filename`, `pdf_file`, `pdf_filename`.

- Si alguna cambia de valor y el wizard estaba en `previewed`, `write()` limpia preview, marca de
  advertencia y huella, y devuelve el estado a `draft`.
- Un vals idéntico al almacenado no invalida (evita ruido del cliente web).
- Asignar el campo en Python también pasa por `write()` ⇒ invalida. La única vía que **no** invalida es una
  escritura de bajo nivel (`_write`/SQL directo): para ese caso existe la comparación de huella en la guarda.

### 13.4 Documentos requeridos

`has_required_documents` (compute) gobierna el botón «Leer documento»:

- Modalidad **normal**: PDF/Guía **y** Excel.
- Modalidad **Volúmenes**: al menos uno (PDF o Excel).

Si faltan, `action_preview_document` lanza `UserError` **antes de clasificar**: no se escribe ningún campo.

### 13.5 Fuera de alcance

`_onchange_intake_modality_patio` sigue diferido (R6): cambiar de modalidad no reasigna el patio.

### 13.6 Descarte de fila de totales de cierre sin etiqueta (Regla V1 — AD-136)

En packings Excel que contienen una fila final de totales puramente numérica sin la etiqueta "TOTAL" o "SUBTOTAL" (caso paradigmático de la guía `40030.xls`), el motor de extracción `document_extractor.py` la aceptaba como una línea adicional de detalle (línea 13), propagando lotes sintéticos y duplicando el volumen extraído (92,316 m³ frente a los 46,158 m³ reales).

**Comportamiento en la vista previa del Asistente de Ingreso:**
- **Vista previa de Producto:** La invocación a `extract_document()` en `action_preview_document()` descarta automáticamente la fila de cierre mediante la Regla V1 (`_is_unlabeled_total_row` con acumulador `running_total_m3` y tolerancia absoluta `0.01` m³). La previsualización de 40030 pasa de 13 líneas y 92,316 m³ a **12 líneas y 46,158 m³**.
- **Modalidad Volúmenes con Excel:** Se extrae el detalle exacto sin líneas fantasmas, eliminando la falsa discrepancia entre el PDF y el Excel.
- **Trazabilidad:** La fila omitida genera la advertencia `"Fila N: fila de totales sin etiqueta omitida (volumen {v} ≈ suma acumulada {s})"`.

**Mejora futura de consistencia:**
Se registra como pendiente evaluar un chequeo de consistencia cruzada entre lo que previsualiza el asistente (`extract_document`) y lo que crea el parser final de Producto (`reception_parser.py`), así como usar la columna de volumen nominal de la fila de cierre exclusivamente como dato de contraste y auditoría.


