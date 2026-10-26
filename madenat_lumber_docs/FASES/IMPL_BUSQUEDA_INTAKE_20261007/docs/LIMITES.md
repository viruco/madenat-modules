# LIMITES — Alcance real, decisiones pendientes y lo NO hecho

## 1. Límites de plataforma

- **Filtros "radio" no soportados; los toggles NO son excluyentes.** El RNG de Odoo 18
  (`base/rng/common.rng`) **no admite el atributo `group` en `<filter>`** (solo existe
  en `<field>`). Por eso la modalidad Producto/Procesado/Volúmenes queda como **tres
  toggles INDEPENDIENTES** (no mutuamente excluyentes): el usuario **puede marcar
  varios a la vez** y Odoo los combina por **AND**; marcar **dos modalidades distintas
  produce intersección vacía (0 resultados)** — verificado en aislamiento por
  `test_09_combinacion_modalidad_por_and`. No es un defecto introducido: es una
  limitación del framework. Alternativa posible (no aplicada): un único
  `<filter domain="[('ingestion_type','in',[...])]">`. Falta confirmar el comportamiento
  visual exacto en navegador (V3).

## 2. Decisiones pendientes (documentadas, no implementadas)

- **Volumen numérico:** NO se añade búsqueda por m³. Campo oficial identificado para
  una fase posterior: **`official_volume_m3`** (jerarquía PDF > Excel > Packing;
  expuesto como `official_volume_effective_m3`), **unidad m³**. Falta decidir si se
  expone (columna real) y con qué semántica (0 vs desconocido).
- **Agrupación de Producto:** `product_filter_id` es **solo de búsqueda** (un ingreso
  puede tener varios productos → no es una columna agrupable sin inventar un criterio).
  Se decidió NO agrupar por producto para no elegir arbitrariamente "el primero".
- **Procesador:** proviene **solo** de `toll.processing_order.processor_id` vía
  `madenat.guia.processing.toll_order_id`. Las guías de Producto y las que no tienen
  orden toll quedan con `processor_id` vacío. Falta decisión de negocio sobre otras vías.
- **Estados Abiertos/Finalizados** no se ampliaron a `processed`/`error` (se añadieron
  filtros dedicados en su lugar); ampliarlos es una decisión de doctrina pendiente.

## 3. Lo que NO se cambió (por alcance/seguridad)

- **Sin** cambios en ACL, ingesta, stock, costes ni contabilidad.
- **Sin** cambios en CANON ni en datos históricos.
- **`id` y `source_res_id` intactos** (regla de la Consola). El JOIN añadido es **1:1**
  (`toll_processing_order`), no multiplica filas.
- **No** se usa `sudo`; no se exponen documentos/proveedores no autorizados.
- **No** se normalizan ni fusionan referencias históricas de OC.
- **No** se aplicó al entorno activo; **no** hubo commit/push.

## 4. Notas sobre la prueba aislada

- Se usó **`-u` (update)** sobre una base **clon de plantilla**, no `-i`, porque la
  vista de lista referencia `action_madenat_lumber_intake_new` **definida más abajo en
  el mismo fichero** (referencia hacia adelante **preexistente** del módulo): en una
  base vacía esa referencia falla; en una base con el módulo ya instalado resuelve.
  **No** es un defecto introducido por este cambio.
  - *Recomendación separada (fuera de este alcance):* si se desea soportar
    instalación en base limpia, mover el `<record id="action_madenat_lumber_intake_new">`
    antes de la lista (cambio de orden, sin semántica).
- **V3 (navegador) no ejecutada.** La coherencia columna/búsqueda/agrupación y la
  navegación se validaron **V1 (XML)** y **V2 (ORM/SQL)**; falta la comprobación visual.

## 5. Riesgos residuales

- La agrupación por `oc_documental` (texto) puede crear grupos por variantes de
  formato de la misma OC ("MC - 2506 - 01" vs "MC250601"): **intencional** (no se
  normaliza). Es coherente con la doctrina de no fusionar referencias.
- `guide_date_kind` clasifica la fuente, **no** añade una segunda fecha; `guide_date`
  conserva su semántica mixta (documental u operativa) ahora explícita.
- Un cambio futuro del RNG o de `toll_processing_order` requeriría revisar el JOIN.

## 6. Qué falta exactamente para aplicar

1. **Autorización** de aplicación al entorno activo.
2. **V3 (navegador)** de la nueva búsqueda/agrupaciones con usuario operativo.
3. Confirmación de las decisiones pendientes de §2 (sobre todo Volumen y Procesador).
