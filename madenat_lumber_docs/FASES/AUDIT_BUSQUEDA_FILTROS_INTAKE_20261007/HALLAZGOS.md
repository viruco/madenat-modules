# HALLAZGOS — Búsqueda, filtros y agrupaciones de Intake

Severidades: **Alta** = dato engañoso o filtro que no hace lo que aparenta; **Media** = cobertura/semántica incompleta; **Baja** = cosmético/documental.
Categorías (para `PROPUESTA_MINIMA.md`): **A**=solo XML; **B**=campo ya disponible; **C**=dato existe en origen pero no en consola; **D**=concepto ambiguo/inexistente.

---

## H-01 (Alta · A/B) — "OC documento" no muestra la OC documental

- **Qué:** la columna y la búsqueda textual "OC documento" (`purchase_reference`) muestran el **nombre de la OC vinculada** cuando existe, no la referencia extraída del documento.
- **Evidencia (código):** `intake_console.py:528` (`lr.purchase_order`) y `:545` (`COALESCE(po.name, gp.oc_reference_raw, '')`). Para producto, `lumber_reception._compute_purchase_order_display` prioriza `purchase_id.name` -> `manual_po_name` -> `oc_reference_raw` -> `'SIN ORDEN'`.
- **Contradicción:** el modelo declara `oc_reference_documental` que lee **exclusivamente** `oc_reference_raw` (`intake_console.py:89`), y la doctrina dice que `oc_reference_raw` "NUNCA se sobrescribe al vincular una `purchase.order`" (`madenat_guia_processing.py:643`). La columna, en cambio, sí privilegia el vínculo.
- **Impacto:** dos conceptos distintos comparten la etiqueta "OC documento"; el operador busca por referencia documental pero el texto servido puede ser el de la OC interna.
- **Propuesta:** separar etiquetas ("OC documental" = `oc_reference_documental`, "OC vinculada" = `purchase_id`) y alinear el texto de la columna con el dato documental real (ver PROPUESTA §1).

## H-02 (Alta · A) — La agrupación "OC" agrupa por un campo vacío

- **Qué:** el grupo "OC" (`group_purchase`) usa `{'group_by':'purchase_id'}` (OC vinculada), mientras la columna muestra `purchase_reference`.
- **Evidencia (base activa 2026-10-07):** de **18 filas**, `purchase_id` es NULL en **las 18** (con vínculo=0, con referencia sin vínculo=15, sin OC=3). Por tanto la agrupación "OC" produce **un único grupo vacío "(No definido)"**, aunque la columna lista 15 referencias.
- **Impacto:** es exactamente "agrupar por un campo vacío mientras la columna muestra otro dato". El usuario cree que agrupa por la OC que ve.
- **Propuesta:** si la intención es agrupar por OC **documental**, usar la referencia documental; si es la **vinculada**, rotular "OC vinculada". Ver PROPUESTA §2. No normalizar/fusionar referencias históricas.

## H-03 (Alta · A) — Etiqueta ambigua "OC" (dos conceptos)

- **Qué:** en la lista la columna se llama "OC documento" pero la agrupación se llama "OC" y el form usa tres rótulos ("OC documento", "OC vinculada", "OC" para `oc_pending`).
- **Impacto:** no queda claro qué filtra/agrupa el botón "OC".
- **Propuesta:** etiquetas inequívocas: **"OC documental"** y **"OC vinculada"** en columna, búsqueda y agrupación. Ver PROPUESTA §1–§2.

---

## H-04 (Media · A/B) — "Fecha" tiene significados distintos según el origen

- **Qué:** `guide_date` = Producto: `COALESCE(guia_fecha, reception_date::date)` (emisión de guía o fecha de recepción truncada); Procesado/Volumen: `date_emission` (emisión de guía).
- **Evidencia:** `intake_console.py:525,542`; campos `lumber_reception.py:1087,1101`, `madenat_guia_processing.py:626`.
- **Impacto:** la columna/agrupación "Fecha" mezcla fecha documental y fecha operativa; no es comparable entre orígenes. Producto además usa un `Datetime` truncado (posible efecto de zona horaria al `::date`).
- **Propuesta:** etiquetar como "Fecha de guía" y documentar la prioridad; no hardcodear fechas; conservar los controles nativos de rango y los `:day` (compatibles con Date). Ver PROPUESTA §3.

## H-05 (Media · C/D) — "Producto" es modalidad; el producto real no es consultable

- **Qué:** el filtro "Producto" es `ingestion_type='product'` (modalidad). El producto real de cabecera (`intake_console.product_id`) es `store=False` y solo aparece en el form si **todas** las líneas coinciden; los productos de línea viven en `*.line.product_id`.
- **Evidencia:** `intake_console.py:498-511,1424-1435`; líneas en `lumber_reception.py:55` y `madenat_guia_processing.py:80`.
- **Impacto:** no se puede buscar/agrupar por producto real; no se puede resolver "¿qué ingresos contienen el producto X?".
- **Propuesta:** NO elegir el primer producto de línea; evaluar exponer un filtro de producto que consulta **líneas** sin duplicar filas (categoría C). Ver PROPUESTA §4.

## H-06 (Media · C/D) — No hay "Procesador" en la consola

- **Qué:** "Procesado" es modalidad, no quién procesó. No existe campo/filtro/agrupación de procesador.
- **Evidencia:** doctrina CANON/19 §2 (`res.partner.is_processor`); `toll.processing.order.processor_id`; `madenat.guia.processing.toll_order_id` (`guia_processing_integration.py:15`); `res.partner.processor_location_id` (`madenat_processor_location.py`). La consola solo trae `partner_id` ("Proveedor / Transportista").
- **Impacto:** imposible filtrar por planta procesadora; `partner_id` no es evidencia del rol.
- **Propuesta:** no usar `supplier_id`/`partner_id` como procesador. Mostrar la necesidad concreta (categoría C) y decidir con negocio si el procesador de una guía proviene de `toll_order_id.processor_id`. Ver PROPUESTA §5.

## H-07 (Media · C/D) — "Volúmenes" es modalidad; no hay búsqueda numérica

- **Qué:** "Volúmenes" = `ingestion_type='volume'` (guías `granel`), correcto y exacto. Pero ningún volumen (oficial/documental/calculado) es columna SQL (`store=False`), así que no hay búsqueda ni rangos por m³.
- **Evidencia:** `intake_console.py:525,539`; campos de volumen `store=False` (`:293, `:162, etc.`); CANON/17 distingue NOMINAL/DISPONIBLE/EXPORTACIÓN/OFICIAL.
- **Impacto:** no se puede aislar "ingresos con m³ > X" ni distinguir volumen documental de calculado en búsqueda.
- **Propuesta:** no añadir umbrales; si se necesita, exponer un campo de volumen **documental oficial** consultable (categoría C) con su unidad (m³) y distinguir "0" de "desconocido". Ver PROPUESTA §6.


---

## H-08 (Media · A) — Rótulos de estado que no aplican a ambos orígenes

- **Qué:** "Recibido" (`state='done'`) solo existe en `lumber.reception`; "Validado" (`state='validated'`) solo en `madenat.guia.processing`. Ninguno cubre ambos flujos.
- **Evidencia (base activa):** "Recibido" -> **0 filas**; "Validado" -> 7 filas (5 processed + 2 volume). Selecciones nativas: `lumber_reception.py:947` (tiene `done`, no `validated`); `madenat_guia_processing.py:617` (tiene `validated`, no `done`).
- **Impacto:** el mismo botón de estado visible no significa lo mismo según el ingreso. Estados sin cobertura en filtros: guía `processed` ("Procesada (legacy)") y `error` (Producto) no caen en ningún filtro específico ni en Abiertos/Finalizados.
- **Propuesta:** no equiparar estados sin doctrina; añadir etiquetas/dominios coherentes (o nota de alcance) para `processed` y `error`. Ver PROPUESTA §7.

## H-09 (Media · B) — "Revisión" (`review_state`) no es filtrable ni agrupable

- **Qué:** la lista muestra `review_state` (Listo para stock / Requiere revisión / Pendiente documental / Enviado a stock) pero es `store=False` (compute) → sin control de filtro/agrupación.
- **Evidencia:** `intake_console.py:146` (Selección compute) y ausencia de filtros para ello en la vista de búsqueda (1866).
- **Impacto:** no se puede trabajar por "Requiere revisión" / "Listo para stock" desde la barra de búsqueda; es un microestado clave para el operador.
- **Propuesta:** si se quiere filtrar, requiere `search` method o campo `store=True` (categoría B/C, con coste ORM). Ver PROPUESTA §8.

## H-10 (Baja · A) — Combinación de filtros por AND (sin OR)

- **Qué:** los filtros son toggles independientes sin atributo `group`; seleccionar dos modalidades a la vez (Producto + Procesado) da intersección **vacía**.
- **Impacto:** el usuario puede esperar un OR y obtener 0 resultados.
- **Propuesta:** documentar; si se quiere OR, un único `<filter domain="[('ingestion_type','in',...)]">` o agrupar con `group=`. Requiere confirmación en navegador (V3). Ver PROPUESTA §9.

## H-11 (Baja · Informativo) — No hay `ir.filters` guardados

- **Evidencia:** `SELECT ... FROM ir_filters WHERE model_id='madenat.lumber.intake.console'` -> **0 filas** (la base tiene 9 filtros en total, ninguno de esta consola).
- **Impacto:** ningún favorito/filtro guardado altera la sesión. **No se crean ni modifican** (restricción de seguridad).

## H-12 (Media · C/D) — Sin aislamiento por compañía/permisos en la vista SQL

- **Qué:** la vista SQL no tiene `company_id` ni filtro de compañía; el ACL es por modelo (Operaciones r/w; Auditoría y Contabilidad r). El menú está limitado a `group_madenat_operaciones`.
- **Evidencia:** columnas de la vista (11, sin `company_id`); ACL id 3712/3768/3769; `ir_ui_menu_group_rel` (menú 500 -> Operaciones). README §17 declara "sin aislamiento multiempresa".
- **Impacto:** en entorno multiempresa, todos los registros serían visibles a quien tenga acceso al modelo. No se añade `sudo` ni se exponen datos: es un límite del diseño actual (single-company).
- **Propuesta:** registrar el límite; no cambiar ACL/SQL en esta auditoría.

## H-13 (Baja) — Rendimiento: vista sin índices, computes por fila

- **Qué:** la consola es una vista SQL (sin índices propios) y varios campos son compute por fila (posible N+1). Riesgo R5 del README (`intake_console.py` computes).
- **Impacto:** sin evidencia de problema con 18 filas. **No** se crean índices ni se ejecutan cargas intensivas.

---

## Resumen de severidades

| Hallazgo | Sev | Categoría | Tema |
|---|---|---|---|
| H-01 | Alta | A/B | OC documento engañoso |
| H-02 | Alta | A | Agrupación OC por campo vacío |
| H-03 | Alta | A | Etiqueta "OC" ambigua |
| H-04 | Media | A/B | Semántica de Fecha |
| H-05 | Media | C/D | Producto real no consultable |
| H-06 | Media | C/D | Procesador ausente |
| H-07 | Media | C/D | Volumen no consultable |
| H-08 | Media | A | Estados que no aplican a ambos orígenes |
| H-09 | Media | B | review_state no filtrable |
| H-10 | Baja | A | Combinación AND |
| H-11 | Baja | — | Sin filtros guardados (informativo) |
| H-12 | Media | C/D | Sin aislamiento por compañía |
| H-13 | Baja | — | Rendimiento (sin evidencia) |

