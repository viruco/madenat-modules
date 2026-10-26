# COMPARACIÓN DOCUMENTAL — guía 15183 (Recepción 1369 vs Guía 33154)

Lectura de datos reales de `madenat_test` (sólo `SELECT`). Identificadores y
hashes; sin exponer documentos completos.

## 1. Cabeceras

| Campo | Recepción `lumber.reception` id 1369 | Guía `madenat.guia.processing` id 33154 |
|---|---|---|
| Número | `15183` (`name` = `guia_numero`) | `15183` (`name`) |
| Emisor | `supplier_id = 1052` | `partner_id = 1052` |
| Emisor nombre/RUT | `Proveedor 13.159.180-2` / `13.159.180-2` | idem (`supplier_resolution_note`) |
| Tipo real | Producto (`ingestion_profile=f5085`) | Procesado (`tipo_recepcion=service`) |
| Estado | `verified` | `verified` |
| `create_date` | 2026-09-03 00:21:20 (`create_uid=2`) | 2026-10-07 20:40:56 (`create_uid=8`) |
| OC/referencia | — (`purchase_id` vacío) | `oc_reference_raw = MC 1108-326` (norm `MC1108326`, `not_found`) |
| Volumen | (staging) | `vol_comercial 50.863` / `vol_total_m3 42.054` |

## 2. Adjuntos (`ir.attachment`: `name` + `checksum` SHA-1)

| Origen | `name` (field) | `checksum` |
|---|---|---|
| Recepción 1369 | `pdf_file` | **`0fa994e5f3e215cd588fc971745e0e3ea0847553`** |
| Recepción 1369 | `excel_file` | `965f54d4401728f301feb9dba20bc038afab20a1` |
| Guía 33154 | `guide_pdf_file` / `GUIA 15183 MADENAT 02-09-2026.pdf` | **`0fa994e5f3e215cd588fc971745e0e3ea0847553`** |
| Guía 33154 | `excel_file` / `15183.xls` | `82eab5a2ff2624cd72b454f8cb1f88ffd3f0eba7` |
| Guía 33152 (eliminada) | PDF / Excel | `0fa994e5…` / `82eab5a2…` (mismos) |

- **[V] El PDF es byte-idéntico en Recepción y Guía** (mismo SHA-1) → el mismo
  archivo físico `GUIA 15183 MADENAT 02-09-2026.pdf` se usó en ambos flujos.
- **[V] El Excel difiere** (re-guardado). **No** se exige coincidencia de checksum
  para reconocer el mismo documento.

## 3. Contenido / líneas

| Recepción 1369 (`lumber_reception_line`) | Guía 33154 (`madenat_guia_processing_line`) |
|---|---|
| 13 líneas | 13 líneas |
| `lot_name` = `0000000000439`…`0000000000450` | `lot_name` = `1`…`12` (índice) |
| piezas: 348,232,203,290,232,232,232,**240,50**,232,290,203,232 | **idéntico** |

- **[V]** El **desglose de piezas por línea coincide uno a uno y en el mismo
  orden**, incluida la **línea repetida** del lote `…446` (240 + 50). El número de
  lotes únicos (`12`) también coincide con los `stock.lot` 2614-2625 de la
  recepción.

## 4. Clasificación de la relación

**[V] Mismo documento** (mismo número + mismo emisor + mismo PDF + mismo desglose).
No es:
- *mismo documento en archivos diferentes* → aunque el Excel difiere, el **PDF es
  idéntico** y el contenido coincide;
- *documentos distintos con número coincidente* → el emisor es **el mismo** (id 1052);
- *evidencia insuficiente* → hay tres coincidencias independientes.

## 5. Lo que NO se concluye

- El **nombre de archivo** (`02-09-2026`) **no** prueba por sí solo la fecha
  documental **[V]/[I]**; la fecha se infiere del PDF.
- La **fecha de ingreso** (`create_date`) **no** demuestra documento distinto.
- El **modelo/flujo distinto** (Recepción vs Procesado) **no** demuestra que sean
  documentos diferentes (al contrario, aquí son el mismo).

## 6. Conclusión para el control

Bajo la identidad **`número + emisor`**, ambos registros son **el mismo documento**.
El control de duplicado debió **bloquear** el segundo ingreso (Procesado), aunque el
primero (Recepción 1369) estuviera **sin stock** y con staging. Hoy **no lo hace**
(ver `RESULTADOS_REPRODUCCION.md`).
