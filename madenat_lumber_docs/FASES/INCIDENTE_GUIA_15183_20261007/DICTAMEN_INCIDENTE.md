# DICTAMEN — Incidente de ingreso repetido de la guía 15183

**Proyecto:** MADENAT Lumber — Odoo 18 CE · `/home/viruco/dev-stack/odoo/odoo-18-ce`
**Fecha:** 2026-10-07 · **Alcance:** diagnóstico focalizado + reproducción aislada.
**Sin cambios en el entorno activo** (código, ACL, CANON, datos). No commit/push.

Clasificación de evidencia: **[V]** hecho verificado (archivo+línea o consulta de
lectura) · **[I]** inferencia · **[U]** incertidumbre / dato faltante.

---

## 0. Resumen ejecutivo (una línea)

La ingesta pasó porque **la comprobación de duplicado *confirmado* de la ruta
Procesado usa `cross_model=False`** (`reception_parser._check_guide_duplicate`) y
por tanto **sólo inspecciona `madenat.guia.processing`**: la **Recepción 15183**
(`lumber.reception` id 1369, mismo emisor 1052) **fue encontrada** por la llamada
de *aviso* (`cross_model=True`) pero esa llamada es **no bloqueante**
(`raise_on_match=False`) → sólo dejó un mensaje en el chatter y **nunca bloqueó**.

---

## 1. ¿Los dos ingresos representan el mismo documento?

**[V] Sí — mismo documento, con alta confianza.**

| Evidencia | Recepción 1369 (`lumber.reception`) | Guía 33154 (`madenat.guia.processing`) |
|---|---|---|
| Número | `15183` | `15183` |
| Emisor (`partner_id`) | `1052` | `1052` = `Proveedor 13.159.180-2` / RUT `13.159.180-2` |
| **PDF** (`ir_attachment.checksum`) | `0fa994e5…87553` | `0fa994e5…87553` (**idéntico**) |
| Desglose de piezas (13 líneas) | 348,232,203,290,232,232,232,**240+50**,232,290,203,232 | **idéntico, mismo orden** |
| Excel (`checksum`) | `965f54d4…20a1` | `82eab5a2…0eba7` (distinto) |

El **PDF tiene el mismo SHA-1** en ambos flujos y el **desglose de piezas coincide
uno a uno** (incluida la línea duplicada del lote `…446` = 240+50). El Excel
difiere (re-guardado), lo que **no** desmiente la identidad (no se exige checksum).
**[I]** la fecha documental real es la del PDF (`02-09-2026`); `date_emission`
guardada (`2026-10-07`) es la fecha de ingesta por defecto.

> El caso (Recepción 15183 existente, `state=verified`, con staging y **sin stock**
> propio) se reproduce sobre las **filas reales** en `RESULTADOS_REPRODUCCION.md`
> (test `E1`).

---

## 2. ¿Por qué pasó la ingesta?

**[V] Ruta real:** `_route_procesado` (`madenat_lumber_intake/models/intake_wizard.py:683-706`)
crea la guía **sin** `name` ni `partner_id` y luego llama `guia.action_verify_data()`:

```python
guia = self.env['madenat.guia.processing'].create(vals)   # sin name / sin partner
guia.action_verify_data()                                 # lee PDF/Excel y fija identidad
```

- En `create()` la identidad es incompleta → `_check_guide_identity_duplicate_on_create`
  **no valida** (`madenat_guia_processing.py:3390-3395`).
- `action_verify_data` **fija `name`+`partner_id` en un único `write(update_vals)`**
  (`madenat_guia_processing.py:1800-1930`). Ese `write` dispara
  `_check_guide_identity_duplicate` (`:3307-3376`):
  - **Bloqueo** (`:3358-3364`): `cross_model=False` → **sólo mira `madenat.guia.processing`** → la Recepción es invisible → **no bloquea**.
  - **Aviso** (`:3367-3376`): `cross_model=True, raise_on_match=False` → **sí ve la Recepción** pero **no bloquea**; publica el chatter.

**[V] Log del intervalo** (`logs/incidente_window_log.txt`, guía 33154):

```
2026-10-07 20:41:00,321 ... _check_guide_duplicate: guía=15183 company=1 partner=1052
     exclude=33154@madenat.guia.processing cross_model=False
2026-10-07 20:41:00,323 ... ✅ _check_guide_duplicate: sin duplicados para guía=15183
2026-10-07 20:41:00,323 ... _check_guide_duplicate: guía=15183 company=1 partner=None
     exclude=33154@madenat.guia.processing cross_model=True
```
La llamada de bloqueo reportó «sin duplicados»; la de aviso **no** (retornó el
hallazgo) → encontró la Recepción y **sólo advirtió**. **[V]** el chatter de la
guía 33154 contiene `⚠️ Número de guía coincidente … (Recepción directa)`
(`mail_message` 136426).

La guía se ingreso **tres veces** (mismo PDF): id 33152 (2026-10-06 18:51,
eliminada), 33153 (2026-10-07 19:23, eliminada), 33154 (2026-10-07 20:40, viva).
La tercera ocurrió **después** de aplicar el fix (módulo `write_date`
`2026-10-07 20:34:57`) → el código activo **aún permite** el duplicado.

---

## 3. ¿La búsqueda omite staging o depende de stock?

**[V] No depende de stock ni de materialización.** El dominio de
`_check_guide_duplicate` (`reception_parser.py:96-107`) es
`[('name','=',guide_no), ('company_id','=',company_id)]` sobre `lumber.reception`
**sin** filtro de `state`, lotes, pickings ni movimientos, y con `sudo()` → busca
**cabeceras** aunque no tengan stock. **[V]** `madenat.guia.processing` **no tiene**
`company_id` (`:143-149` degrada a `name`). → **El documento fue encontrado; la
omisión es de alcance (`cross_model=False`), no de staging.**

---

## 4. ¿La política cross-model fue demasiado permisiva?

**[V] Sí (para el caso documento-idéntico).** El AJUSTE B del cierre previo
(`FASES/FIX_GUIA_DUP_CIERRE_20261007_170340/docs/INFORME_CIERRE.md`) llevó
`cross_model` a **default `False`**: una coincidencia de número entre flujos **ya
no bloquea en ningún sentido**. Correcto para **homónimos** (emisor distinto),
incorrecto para el **mismo documento** (mismo `número+emisor`).

**[V] La doctrina citada no sostiene la exclusión por modelo.** `CANON/12 §5.2`
prohíbe usar `guia_number` como **discriminador de origen de lotes**; no dice que
el **número** no pueda usarse para **detectar** un documento ya ingresado.
`CANON/12 §2/§3.3` define la identidad por **relaciones/cabecera**. → **Conflicto
doctrinal explícito** (ver `PROPUESTA_MINIMA.md §D`).

---

## 5. ¿Cuál es el punto mínimo para corregirlo?

**[V] Un único punto: la comparación de identidad en `_check_guide_duplicate`**
(`madenat_lumber_core/models/reception_parser.py:32-189`) y el `cross_model` de sus
llamadores de bloqueo. Hoy el bloqueo compara **sólo por `name` dentro del propio
modelo**; debe comparar por **`name` + emisor** a través de **ambos** modelos
(bloquear sólo si el emisor coincide; advertir si difiere). Firma exacta en
`PROPUESTA_MINIMA.md`.

---

## 6. ¿Qué efectos ya existen y cuáles no?

- **[V] Existen:** cabecera de la guía 33154 (`state=verified`), **13 líneas de
  staging** (`madenat_guia_processing_line`), 4 adjuntos (PDF/Excel + duplicados),
  2 mensajes de chatter.
- **[V]** la recepción 1369 tiene 13 líneas, **12 lotes** (`stock_lot` 2614-2625) y
  el **picking 436** (`EMB-00227`, `done`).
- **[V] No existen:** **ningún** `stock.lot` con `guia_processing_id` de
  33152/33153/33154 (0 lotes de la guía); sin movimientos ni quants de la guía.
  → efectos de la guía = **cabecera + staging + chat + adjuntos; NO materializó stock.**
- **[V]** 33152 y 33153 fueron canceladas (Modo B) y eliminadas (Modo A,
  `guia_delete_permanent`); la reversión tocó el picking **436** de la **recepción**
  («Albaranes para '15183': 1 → EMB-00227»).

---

## 7. ¿Qué prueba anterior dejó escapar el defecto?

**[V]** `tests/test_guide_duplicate_ingest.py::test_03_cross_model_homonym_not_blocked`
(L124) crea una **Recepción `HOM-01` con `partner_a`** y luego una **Guía `HOM-01`
con el MISMO `partner_a`** y **afirma que NO debe bloquear**: es **exactamente el
incidente**, con la **expectativa invertida** (se trató por **modelo**, no por
**identidad**). `test_28_cross_model_symmetric_not_blocked` (L367) consagra la
simetría no bloqueante. **[V]** la suite **no cubrió** «staging sin stock + mismo
emisor + documento idéntico». La prueba nueva (`PRUEBA_REGRESION…`, tests `R1`/`R2`)
**falla con el código actual**.

---

## 8. ¿Qué explica la doble notificación?

**[V] Única fuente** del texto `Ingreso Procesado` (`intake_wizard.py:503-514`),
emitida por `action_preview_document` con `sticky: True` — **una por clic en «Leer
documento»**. **[V]** botón único (`intake_wizard_views.xml:9-14`) y **ninguna**
acción encadenada / `onchange` que la reedite. **[I]** las dos notificaciones
idénticas corresponden a **dos ejecuciones/reintentos** (coherente con las **tres**
ingestas 33152/33153/33154); `sticky` → se acumulan. **[U]** no hay log de cliente
web que pruebe el doble clic exacto. **[V]** la doble notificación **no** crea
cabeceras; se relaciona con **reintentos**, no con la duplicación de cabecera.

---

## 9. ¿Qué explica el ID inexistente 900033152?

**[V] `900033152 = 900000000 + 33152`.** `CONSOLE_ID_OFFSET = 900000000`
(`madenat_lumber_intake/models/intake_constants.py:12`); la Consola genera el `id`
Procesado como `CONSOLE_ID_OFFSET + madenat_guia_processing.id`
(`intake_console.py:26,536`) y la navegación de retorno usa
`res_id = CONSOLE_ID_OFFSET + self.id` (`intake_guia_processing.py:275`;
`intake_wizard.py:1122`). **33152 fue eliminada** (`madenat_audit_log` id 21743,
`guia_delete_permanent`, 2026-10-07 19:23:40) → el `id` de Consola `900033152`
quedó **huérfano** (la vista SQL ya no devuelve la fila) → «registro inexistente».
**[I]** referencia obsoleta a la guía **anterior eliminada**, no un fallo de
resolución de origen ni caché del navegador. **No** se corrige con ID hardcodeado.

---

## Cierre

> **La ingesta pasó porque** la comprobación de duplicado confirmado de la ruta
> Procesado sólo inspecciona su propio modelo (`cross_model=False`); la Recepción
> homónima del **mismo emisor** quedó invisible al bloqueo.
> **El control sobre staging/cabecera** no depende de stock (sí busca cabeceras),
> pero **excluye por modelo**: encontró la Recepción sólo en la llamada de aviso
> no bloqueante.
> **La intervención mínima propuesta es** comparar por **identidad (`name` +
> emisor)** a través de **ambos** flujos en el **punto único**
> `_check_guide_duplicate` (+ `cross_model=True` en los llamadores de bloqueo), en
> `madenat_lumber_core/models/reception_parser.py`, manteniendo el aviso para
> homónimos de emisor distinto.
> **Los registros reales no fueron modificados.**

