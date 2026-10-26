# PROPUESTA_MINIMA — Intervención mínima sobre búsqueda de Intake

**Principio:** mínimo cambio posible; priorizar **A (solo XML)** y **B (campo ya disponible)**. No rediseñar la consola, no crear modelos ni asistentes, no tocar ingesta/stock/costes/contabilidad, no hardcodear IDs/proveedores/fechas, no usar `sudo`.
**Estado:** PROPUESTA. **No implementada** (auditoría de solo lectura).

Categorías: **A**=solo XML; **B**=campo ya disponible (exponerlo bien); **C**=dato existe en origen pero no en consola (requiere extensión acotada); **D**=concepto ambiguo/inexistente (decisión).

---

## 1. OC — etiquetas inequívocas y agrupación coherente (A / B) · PRIORIDAD 1

**Problema (H-01/H-02/H-03):** columna/búsqueda "OC documento" muestra el vínculo; la agrupación "OC" agrupa por `purchase_id` (vacío en las 18 filas).

**Opción mínima A (solo XML, sin tocar SQL ni ORM):**
- Renombrar en la **vista de búsqueda** y en la **lista** para no prometer "documental":
  - `purchase_reference` -> string **"OC (referencia mostrada)"** o, si se acepta la mezcla, **"OC vinculada/documental"**.
  - `purchase_id` -> **"OC vinculada"** (ya lo está en la búsqueda; unificar en columna).
- Reetiquetar la agrupación `group_purchase` a **"OC vinculada"** (es lo que realmente agrupa) y, si se necesita agrupar por texto, exponer una agrupación **"OC documental"**.

**Opción B (campo ya disponible, sin columna nueva):** `oc_reference_documental` y `oc_documentary_status` ya existen en el modelo (compute `store=False`). Añadir en la búsqueda un `<filter>`/`<group>` que agrupe por documento **requiere `search` method** (los compute `store=False` no agrupan solos) -> ya no es sólo XML puro (pasa a B con un `_search_*`/campo `store=True`). **No crear** si no se aprueba.

**Decisión pendiente:** ¿la operación necesita agrupar por **OC documental** o por **OC vinculada**? (Hoy no hay ningún vínculo; el 100 % de las OC son documentales.)

## 2. Error corregible sin ambigüedad (A) · PRIORIDAD 1

- Rotular la agrupación actual `group_purchase` como **"OC vinculada"** (predicado real: `group_by purchase_id`). Cambio de **solo string** en `intake_console_views.xml`. Elimina la expectativa falsa de que "OC" agrupa por lo que muestra la columna.

## 3. Fecha (A/B) · PRIORIDAD 2

- Renombrar "Fecha" -> **"Fecha de guía"** en columna y agrupación (coherente con `guide_date`). Sólo XML.
- **No** hardcodear años ni fechas; conservar el rango nativo y `guide_date:day`.
- Documentar la prioridad (`guia_fecha` -> `reception_date::date` en Producto; `date_emission` en Procesado). Si se aprueba, un `help=` en el campo.
- **Decisión pendiente:** ¿se quiere además una agrupación por mes/año? (`guide_date:month`/`:year` es compatible con Date y es solo XML.)

---

## 4. Producto real (C) · PRIORIDAD 3 (requiere extensión)

- El producto de cabecera `product_id` es `store=False`; los productos viven en las líneas.
- **No** implementar en esta auditoría elegir "el primer producto". Si se aprueba: exponer un **filtro** que busque en las líneas del origen **sin duplicar filas de consola** (p. ej. `_search` que resuelve sobre `lumber.reception.line.product_id` / `madenat.guia.processing.line.product_id`), o un campo `product_id` de cabecera **store=True** en la vista SQL solo si es semánticamente estable. **Requiere decisión.**

## 5. Procesador (C/D) · PRIORIDAD 3 (requiere decisión)

- No existe en la consola. Se documenta la necesidad concreta **sin implementarla**:
  - Fuente candidata por guía: `madenat.guia.processing.toll_order_id.processor_id` (solo guías de servicio con orden toll).
  - Maestro: `res.partner.is_processor`.
- **No** usar `partner_id`/`supplier_id` como procesador.
- **Decisión pendiente (negocio):** ¿el procesador de una guía proviene de la orden toll? ¿aplica a todas las modalidades?

## 6. Volúmenes (C) · PRIORIDAD 3 (opcional)

- "Volúmenes" como modalidad ya es correcto (A: no tocar).
- Búsqueda numérica por m³ **no es posible hoy** (`store=False`). Si se aprueba, exponer **un** volumen **oficial documental** consultable con su unidad (m³), distinguiendo "0" de "desconocido", **sin** cambiar cálculos ni conversiones. **Requiere decisión.**

## 7. Estados (A) · PRIORIDAD 2

- Documentar/etiquetar que "Recibido" solo aplica a Producto y "Validado" solo a Procesado/Volúmenes (por dominio real).
- Cubrir los estados huérfanos con controles existentes:
  - Añadir filtro **"Procesada (legacy)"** con `[('state','=','processed')]` (solo XML).
  - Añadir filtro **"Error"** con `[('state','=','error')]` (solo XML).
  - Ampliar "Abiertos"/"Finalizados" para incluir `processed`/`error` **solo** si la doctrina lo autoriza. **Decisión pendiente.**

## 8. Revisión (`review_state`) (B/C) · PRIORIDAD 3

- Se muestra pero no se filtra/agrupa (`store=False`). Si se aprueba, añadir `search` method o `store=True` (mayor coste). **Requiere decisión.**

## 9. Combinación de filtros (A) · PRIORIDAD 3

- Los filtros se combinan por **AND**. Si se necesita **OR** entre modalidades, definir un único `<filter domain="[('ingestion_type','in',['product','processed'])]">` o usar `group=`. **Solo XML**. Confirmar en navegador antes.


---

## 10. Qué NO hacer (límites de esta auditoría)

- No introducir IDs/nombres de proveedores o procesadores hardcodeados, ni fechas fijas, ni parámetros innecesarios.
- No crear modelos/asistentes nuevos; no tocar ingesta, stock, costes ni contabilidad; no cambiar cálculos ni conversiones.
- No normalizar ni fusionar referencias históricas de OC; no unir órdenes por parecido de texto.
- No añadir `sudo`; no exponer documentos/proveedores no autorizados.
- No crear índices ni ejecutar cargas intensivas.

## 11. Archivos que requerirían cambio (según categoría)

| Categoría | Cambio | Archivo(s) |
|---|---|---|
| **A** (solo XML) | Reetiquetar OC/Fecha, añadir filtros de estado (processed/error), OR de modalidad | `custom_addons/madenat_lumber_intake/views/intake_console_views.xml` |
| **B** (campo disponible) | Filtrar/agrupar `oc_reference_documental`, `oc_documentary_status`, `review_state` | `intake_console.py` (search methods) + `intake_console_views.xml` |
| **C** (extensión) | Producto real, Procesador, Volumen consultable | `intake_console.py` (`init()` y/o search) — **solo si se aprueba** |
| **D** (decisión) | Definir semántica de Procesador y de agrupación OC | negocio + CANON |

## 12. Intervención mínima recomendada (resumen ejecutable como A/B)

1. **XML** `intake_console_views.xml`: renombrar "OC documento" -> **"OC documental"** solo si se alinea el texto; reetiquetar la agrupación a **"OC vinculada"**; renombrar "Fecha" -> **"Fecha de guía"**; añadir filtros de estado **"Procesada"** y **"Error"**.
2. **Opcional (B):** exponer `oc_reference_documental` como filtro/agrupación "OC documental" mediante un `search` method mínimo (compute `store=False`), sin tocar SQL.
3. Todo lo demás (Producto/Procesador/Volumen/Revisión) queda **documentado y a decisión**, sin implementar.

## 13. Resumen por categoría

| # | Mejora | Cat. | Prioridad |
|---|---|---|---|
| 1 | Etiquetas OC inequívocas (columna/búsqueda) | A | 1 |
| 2 | Agrupación "OC vinculada" (predicado real) | A | 1 |
| 3 | Agrupación/filtro "OC documental" | B | 1 (opcional) |
| 4 | "Fecha de guía" (renombre) | A | 2 |
| 5 | Agrupación por mes/año | A | 2 (opcional) |
| 6 | Filtros de estado huérfanos (processed/error) | A | 2 |
| 7 | Aclarar alcance de "Recibido"/"Validado" | A | 2 |
| 8 | OR entre modalidades (si negocio lo pide) | A | 3 |
| 9 | Filtro por Producto real | C | 3 (decisión) |
| 10 | Filtro/agrupación por Procesador | C/D | 3 (decisión) |
| 11 | Búsqueda numérica de Volumen | C | 3 (decisión) |
| 12 | Filtro por `review_state` | B/C | 3 (decisión) |

