# PLAN_PRUEBAS — Verificación de búsqueda, filtros y agrupaciones de Intake

**Base:** `madenat_test`. **Usuario operativo:** cuenta de `group_madenat_operaciones` (no superusuario). En esta auditoría **no** se ejecutaron pruebas: se definen para la fase de implementación/UAT.

Categorías de verificación (NO mezclar):
- **V1 Estática:** lectura de XML/código. *Una comprobación de XML NUNCA se llama "UI verificada".*
- **V2 ORM/SQL:** `search_count`/`search_read` con el `env` operativo + `SELECT` sobre la vista SQL (solo lectura).
- **V3 Navegador:** comportamiento real del panel de búsqueda (facetas, agrupación, navegación).

---

## 1. Origen Producto (`lumber.reception`)

| ID | Caso | Categoría | Pasos / consulta | Resultado esperado |
|---|---|---|---|---|
| P-01 | Lista muestra recibos de Producto | V2 | `search_count([('ingestion_type','=','product')])` | = filas `product` de la vista (hoy 7) |
| P-02 | Estado mostrado es el del origen | V2 | comparar `state` consola vs `lumber_reception.state` | iguales |
| P-03 | Buscar por N° guía | V2/V3 | buscar por `guide_name` real | 1 fila exacta |
| P-04 | Navegación al origen | V3 | click en fila -> "Modificar origen" | abre `lumber.reception` (fachada Intake) con el `res_id` correcto |

## 2. Origen Procesado / Servicio (`madenat.guia.processing`)

| ID | Caso | Categoría | Pasos / consulta | Esperado |
|---|---|---|---|---|
| PR-01 | Filtro "Procesado" = `service`+`compra`, excluye `granel` | V2 | `search_count([('ingestion_type','=','processed')])` | = no-granel (hoy 6) |
| PR-02 | `cancelled` se muestra como "Cancelado" | V2 | guía cancelada -> `state='cancel'` | 1 fila en grupo Cancelado |
| PR-03 | Estado `processed` (legacy) visible | V2 | guía en `processed` | aparece en la lista; (tras propuesta) filtro propio |

## 3. OC documental vs OC vinculada

| ID | Caso | Categoría | Pasos / consulta | Esperado |
|---|---|---|---|---|
| OC-01 | OC documental sin vínculo | V2 | fila con `oc_reference_raw` y `purchase_id` NULL | texto de OC visible; **no** en grupo "OC" actual |
| OC-02 | OC vinculada | V2 | fila con `purchase_id` | aparece agrupada por OC vinculada; texto de OC = nombre de la PO |
| OC-03 | OC no indicada | V2 | sin `oc_reference_raw` ni `purchase_id` | sin OC; `not_informed` |
| OC-04 | Diferencias de espacios/formato | V2 | `MC - 2506 - 01` vs `MC250601` | no se normaliza/fusiona; se listan por separado |
| OC-05 | Agrupación "OC" no muestra grupo vacío si hay documental | V2 | agrupar por OC (tras propuesta) | grupos por referencia documental, no un único vacío |
| OC-06 | Varias referencias (si el modelo las admite) | V1 | revisar si `oc_reference_raw` es escalar | 1 sola referencia (no multi) |

## 4. Fechas: conocidas y ausentes

| ID | Caso | Categoría | Pasos | Esperado |
|---|---|---|---|---|
| F-01 | Producto con `guia_fecha` | V2 | `guide_date` = `guia_fecha` | coincide con la fecha documental |
| F-02 | Producto sin `guia_fecha` | V2 | `guide_date` = `reception_date::date` | coincide con la de recepción |
| F-03 | Procesado | V2 | `guide_date` = `date_emission` | coincide con la de emisión |
| F-04 | Fecha ausente | V2/V3 | fila con `guide_date` NULL | agrupación "(No definido)"; no rompe rango |
| F-05 | Rango nativo | V3 | filtrar por rango de fechas | filtra sobre `guide_date` (Date) |
| F-06 | Agrupación día/mes/año | V3 | agrupar `guide_date:day`/`:month`/`:year` | jerarquía coherente (Date) |
| F-07 | Filtro vs columna vs grupo | V2/V3 | mismo registro en los tres | mismo valor (coherencia) |

## 5. Producto: modalidad vs producto concreto

| ID | Caso | Categoría | Pasos | Esperado |
|---|---|---|---|---|
| PD-01 | Modalidad vs producto | V1/V2 | "Producto" (filtro) vs `product_id` (form) | modalidad != producto |
| PD-02 | Ingreso con un solo producto | V2 | todas las líneas con mismo `product_id` | cabecera muestra ese producto |
| PD-03 | Ingreso con varios productos | V2 | líneas con `product_id` distintos | cabecera **vacía** (no "primer producto"); **no** duplica filas |
| PD-04 | Búsqueda por producto (tras propuesta) | V2 | buscar ingresos que contengan producto X | lista sin perder registros ni duplicar conteos |

## 6. Procesado vs procesador real

| ID | Caso | Categoría | Pasos | Esperado |
|---|---|---|---|---|
| PX-01 | "Procesado" no implica procesador | V1 | filtro Procesado | devuelve modalidad, no rol |
| PX-02 | `partner_id` no es procesador | V1 | comparar `partner_id` vs procesador real | no se asume igualdad |
| PX-03 | Procesador de guía de servicio | V2 | guía con `toll_order_id.processor_id` | (tras propuesta) filtro por procesador si se aprueba |
| PX-04 | Registros sin procesador | V2 | ingresos sin orden toll | quedan fuera / "(No definido)" sin error |

---

## 7. Volúmenes: modalidad vs medida

| ID | Caso | Categoría | Pasos | Esperado |
|---|---|---|---|---|
| V-01 | Filtro "Volúmenes" = `granel` | V2 | `search_count([('ingestion_type','=','volume')])` | = guías `granel` (hoy 5) |
| V-02 | No mezclar documental y calculado | V1 | revisar campos de volumen | se distinguen por campo/fuente |
| V-03 | Cero vs desconocido | V2 | fila con volumen 0 vs sin dato | no se confunden |
| V-04 | Búsqueda numérica (tras propuesta) | V2/V3 | filtrar m³ oficial > 0 | usa campo con unidad m³; sin umbrales arbitrarios |

## 8. Estados y revisión

| ID | Caso | Categoría | Pasos | Esperado |
|---|---|---|---|---|
| E-01 | Borrador/Verificado/Validado/Recibido/Cancelado | V2 | `search_count` por cada dominio | conteos del inventario (sección 3) |
| E-02 | Abiertos/Finalizados | V2 | dominios `in (...)` | conteos 11 / 7 |
| E-03 | Estado vs Revisión | V1 | `state` (columna) vs `review_state` (columna) | son conceptos distintos; no se equiparan |
| E-04 | `processed`/`error` sin filtro | V2 | filtrar esos estados | (tras propuesta) filtros dedicados |

## 9. Combinaciones de filtros

| ID | Caso | Categoría | Pasos | Esperado |
|---|---|---|---|---|
| X-01 | Dos modalidades a la vez | V2/V3 | Producto + Procesado | AND -> 0 (documentado) o OR si se cambia a `in` |
| X-02 | Modalidad + estado | V2 | Producto + Verificado | intersección correcta |
| X-03 | Fecha + OC | V2 | rango + referencia documental | intersección correcta |
| X-04 | Producto + procesador | V2 | (tras propuesta) | intersección correcta |
| X-05 | Volumen + revisión | V2 | (tras propuesta) | intersección correcta |

## 10. Agrupación, conteos y duplicación

| ID | Caso | Categoría | Pasos | Esperado |
|---|---|---|---|---|
| G-01 | Agrupar por Tipo | V2/V3 | `group_by ingestion_type` | 3 grupos (product/processed/volume) |
| G-02 | Agrupar por OC | V2 | `group_by purchase_id` | hoy 1 grupo vacío (18 filas) — bug H-02 |
| G-03 | Agrupar por Proveedor/Fecha/Estado | V2/V3 | respectivos `group_by` | grupos coherentes |
| G-04 | Conteos sin duplicar por joins | V2 | `count(DISTINCT id)` vs `count(*)` | iguales (hoy 18 = 18) |
| G-05 | Agrupación != AND de columnas | V2 | comparar grupo vs filtro equivalentes | mismo conteo que el filtro |

## 11. Datos incompletos y usuario operativo

| ID | Caso | Categoría | Pasos | Esperado |
|---|---|---|---|---|
| N-01 | Registro con OC vacía | V2 | fila sin OC | "(No definido)"; sin error |
| N-02 | Registro sin origen | V1/V2 | `source_model/res_id` inexistente | `review_state='invalid'`; no rompe la lista |
| N-03 | Permisos reales | V2 | ejecutar con uid operativo (no superusuario) | ve lo permitido; sin `sudo`; sin exponer datos no autorizados |
| N-04 | Multiempresa (si aplica) | V2 | registrar límite | hoy sin aislamiento por compañía (H-12) |

## 12. Navegación al origen tras filtrar/agrupar

| ID | Caso | Categoría | Pasos | Esperado |
|---|---|---|---|---|
| NAV-01 | Abrir origen desde lista filtrada | V3 | filtrar y abrir fila | abre `lumber.reception`/`madenat.guia.processing` correcto |
| NAV-02 | Retorno a la consola | V3 | volver desde la fachada | regresa a "Ingreso de Madera" sin duplicar historial |

---

## 13. Criterios de aceptación (para la futura implementación)

1. Ningún filtro devuelve un resultado cuyo **dato mostrado** no corresponda al **campo filtrado/agrupado** (resuelve H-01/H-02).
2. Los conteos por filtro y por agrupación **coinciden** y no duplican filas.
3. Las etiquetas nuevas ("OC documental"/"OC vinculada", "Fecha de guía") son **inequívocas**.
4. Se preserva la **navegación** al registro origen (V3).
5. Cambios **solo XML** (o `search` method mínimo) — sin tocar SQL/ACL/datos ni usar `sudo`.
6. Pruebas separadas: V1 (estática) ≠ V2 (ORM/SQL) ≠ V3 (navegador). No llamar "UI verificada" a una comprobación de XML.

## 14. Evidencia a adjuntar en la implementación

- Salida de `search_count`/`search_read` por filtro con uid operativo.
- `SELECT` de la vista SQL antes/después (solo lectura) y `arch_db` servido de la vista de búsqueda.
- Capturas/registro de la navegación (V3) para H-02 y NAV-01/02.

