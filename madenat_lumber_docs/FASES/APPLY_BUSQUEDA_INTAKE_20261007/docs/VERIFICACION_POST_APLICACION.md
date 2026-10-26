# VERIFICACION_POST_APLICACION — madenat_test

## 1. Gate del consolidado (antes de aplicar)

- Copia del módulo del **árbol activo** en `IMPL_BUSQUEDA_INTAKE_20261007/gate/`.
- Aplicación de `patch/01..03` → **sin rechazos** (`patch -p1`, 0 `.rej/.orig`).
- `diff -r gate/madenat_lumber_intake artifact/madenat_lumber_intake` → **IDÉNTICO**.
- Inventario: 3 archivos modificados + 1 nuevo (todos dentro de `madenat_lumber_intake`).

## 2. Aplicación (solo `madenat_lumber_intake`)

- Archivos copiados desde el artefacto al árbol activo; verificado `active == artifact`.
- **MD5 activo post** (`logs/hashes_activo_post.txt`):
```
923a69122d4fcabc65bb56f82a590dc3  models/intake_console.py
cf07b72a1977b4d301733bbd583b8e3a  views/intake_console_views.xml
baf2f8ba08f533da87ed117dd2307a21  tests/__init__.py
895b783b6a2800a98ac99ac7ce0c2b1e  tests/test_search_console_oc_fecha_modality.py
```
- Update controlado (`logs/update_madenat_test.log`):
```
madenat_lumber_intake: no translation for language es_CL
Module madenat_lumber_intake loaded in 1.68s, 365 queries
Registry loaded in 11.603s
ERROR/CRITICAL/Traceback/no es válida/RELAXNG: 0
```
- Servicio reiniciado (`docker restart odoo18_app`) → `HTTP:200`.
- Módulo: `madenat_lumber_intake | installed | 18.0.0.11.0`.

## 3. Verificación no destructiva — SQL (solo lectura)

```
view_exists 1 · columns 14
ingestion_type × guide_date_kind:
  product   emission 6 · product reception 1 · processed emission 6 · volume emission 5
rows 18 = distinct_ids 18 · con_oc_doc 15 · con_oc_vinculada 0 · con_procesador 0
columnas: id, source_model, source_res_id, ingestion_type, guide_name, guide_date,
          guide_date_kind, partner_id, purchase_id, purchase_reference,
          oc_documental, state, display_reference, processor_id
```

## 4. Verificación no destructiva — ORM (`odoo shell`, `logs/verify_orm_resultados.txt`)

```
CONSOLE_ROWS 18
TYPE product 7 · processed 6 · volume 5
DATEKIND emission 17 · reception 1
OC_DOC 15 · OC_LINKED 0 · OC_PENDING 15 · OC_NONE 3
COMBO_product_AND_volume 0          (confirmación de la combinación AND)
GROUP ingestion_type 3 · guide_date_kind 2 · oc_documental 15 · processor_id 1
PRODUCT_SEARCH (product 62) -> 2    (búsqueda por producto real, ambos modelos)
ROWS 18 DISTINCT_IDS 18             (sin duplicación de filas)
NAV_ID_OK lumber.reception True ; NAV lumber.reception -> lumber.reception True
NAV_ID_OK madenat.guia.processing True ; NAV madenat.guia.processing -> madenat.guia.processing True
```
- **IDs/offsets intactos**: `id = res_id` (Producto) y `id = 900000000 + res_id` (Procesado).
- **Navegación** a ambos orígenes correcta (`res_model`, `res_id`).
- Vista de búsqueda servida (`ir_ui_view` 1866) contiene `oc_documental`,
  `guide_date_kind`, `filter_oc_pending`, `group_oc_documental`, `group_date_kind`.

## 5. Estado Git y servicios

- **HEAD sin cambios**: `e302c488321c276af7e07f1abeecc8bc261a89f4`. **Sin commit/push.**
- `git status`: 58 entradas. **Delta de esta intervención** (pre→post): exactamente
```
 M madenat_lumber_intake/models/intake_console.py
 M madenat_lumber_intake/views/intake_console_views.xml
?? madenat_lumber_intake/tests/test_search_console_oc_fecha_modality.py
```
  (el resto de las entradas son cambios locales **preexistentes**; `tests/__init__.py`
  ya estaba modificado antes y solo se le añadió 1 línea de import).
- **Servicios**: `odoo18_app` Up (`127.0.0.1:8069`, HTTP 200); `odoo18_db` Up (healthy).

## 6. Qué NO se tocó

ACL, CANON, ingesta, stock, datos históricos, otros módulos. Sin volumen numérico,
sin otros orígenes de procesador, sin cambios en Abiertos/Finalizados, sin commit/push.
