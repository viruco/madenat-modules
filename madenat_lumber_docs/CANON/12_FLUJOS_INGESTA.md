# CANON/12_FLUJOS_INGESTA — Flujos de Ingesta de Madera y Discriminación Operativa

**Proyecto:** MADENAT Lumber — Odoo 18 CE  
**Versión documental:** 1.11.0\
**Fecha de actualización:** 2026-10-17  <!-- 2026-10-17: §12.3 reconocimiento de dimensiones documentales en pulgadas normalizadas S2S (commit 0a89536). Versión 1.10.0 → 1.11.0. -->\
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

### 12.3 Reconocimiento de Dimensiones Documentales en Pulgadas S2S (AD-116/AD-117 — Commit 0a89536)
- **Normalización sin Duplicación de Sobreancho:** En documentos de proveedores como JCE (`NVTA881333` / `GDE 95806`) donde la notación combinada expresa dimensiones comerciales en pulgadas (ej. `5/4x5.3/8x16`), el parser normaliza las dimensiones a milímetros en las líneas de staging ($5,375 \times 25,4 = 136,525\text{ mm}$).
- **Resolución de Ancho en Ingesta:** La función `get_s2s_adjustment()` detecta que $136,525\text{ mm}$ equivale en pulgadas a $5\text{ }3/8"$, correspondiente al valor S2S del nominal rough de 145 mm. En consecuencia, retorna el sobreancho de $+0,125"$ exactamente una sola vez ($5,375 + 0,125 = 5,500"$), garantizando que el volumen documental de la Nota de Venta ($4,997\text{ m}^3$ para 231 piezas) coincida estrictamente con la cubicación del sistema.
