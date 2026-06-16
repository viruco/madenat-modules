# CANON/12_FLUJOS_INGESTA — Flujos de Ingesta de Madera y Discriminación Operativa

**Proyecto:** MADENAT Lumber — Odoo 18 CE  
**Versión documental:** 1.1.0  
**Fecha:** 2026-06-16  
**Estado:** ✅ Vigente — Documento canónico de flujos de ingesta (corregido: `reception_id` como discriminador operativo)  
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

### 3.3 Campo discriminador

```sql
guia_processing_id IS NOT NULL
```

El lote queda vinculado a la guía de procesamiento que lo generó mediante `guia_processing_id`. El método `_compute_reception_type` asigna `reception_type = 'processed'` a estos lotes.

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
*Versión: 1.2.0 — Agregada sección 10: migración picking layer `lumber_reception_id` → `reception_id`.*
