# REDISENO_REGISTRAR_REBAJA_20261010 — Evidencia (rediseño operativo del asistente)

**Fecha:** 2026-10-10 · **Entorno:** `madenat_test` / `odoo18_app` (PostgreSQL `odoo18_db`).
**Naturaleza:** expediente de **evidencia**. Doctrina en `madenat_lumber_docs/CANON/` (`19 §19.18`,
`02 §17.16.16`, `03 §20`, `05`, `INDICE`).

## 1. Solución
Se rediseña la **interfaz del mismo asistente «Registrar rebaja»** (no se crea otro wizard/menú). La
tabla principal presenta el **material del packing list** en columnas separadas y el asistente se abre
como **formulario amplio**. **Interfaz anterior rechazada por Mauricio**; esta entrega queda **pendiente
de su aceptación visual**.

## 2. Mapeo de campos (referencia «DETALLE DEL PACKING LIST»)
| Dato | Modelo.campo | Relación | Unidad | Si falta |
| --- | --- | --- | --- | --- |
| Etiqueta | `stock.lot.ref` | identidad del lote | — | vacío |
| SKU origen | `madenat.guia.processing.line.sku_original` | vía nombre reconstruido | — | «—» |
| Producto | `stock.lot.product_id` | directo | — | vacío |
| Subproducto | `stock.lot.subproducto_id` | directo | — | vacío |
| Espesor/Ancho | `stock.lot.espesor_mm` / `ancho_mm` | directo | mm | 0 |
| Largo | `stock.lot.largo_m` | directo | m | 0 |
| Declarado | `guia.processing.line.espesor_nominal_mm` / `ancho_nominal_mm` / `largo_nominal_m` | vía nombre | mm/m | 0 |
| Piezas | `stock.lot.piezas` | directo | pzs | 0 |
| Volumen documental | `stock.lot.volume_purchase_m3` | directo | m³ | 0 |
| Volumen embarque | `stock.lot.vol_shipment_m3` | directo | m³ | 0 |

**No** existe FK lote↔línea de packing. La asociación usa la **misma regla de promoción**
(`stock.lot.name = etiqueta + SKU + dígitos de la guía`), mapa construido una vez por guía. **No** se
corta el nombre. Verificación de solo lectura sobre la guía real **19827**: 17 lotes → 17 líneas,
**17/17** coincidencias (incluidas etiquetas repetidas D7670/D7717/D7719/D7720/D7721 con largo
distinto).

## 3. Granularidad
Una fila = un `stock.lot` (unidad asignable real). Etiqueta repetida ⇒ **lotes distintos** (no se
deduplican). Disponibilidad por lote (`_i2_lot_available_for_m3`) ⇒ sin doble conteo. El mecanismo
asigna por lote; el material se muestra como subdetalle legible.

## 4. Cambios de vista
`wizards/madenat_sv_imputation_wizard_views.xml`: tabla de material (Seleccionar · Etiqueta · SKU ·
Producto · Subproducto(opt) · Espesor/Ancho/Largo · Piezas · Volumen documental · Disponible ·
Cantidad preparada) + avanzada en columnas **opcionales**; botonera junto a la tabla; cabecera
compacta (SV, guía, saldo documental del SV, seleccionadas, total, resumen); `class="o_xxl_form_view"`;
`target` del **mismo** action `new → current`; FIFO/pendiente a `btn-link`.

## 5. Cantidades y asignación
«Cantidad preparada» es de **solo lectura** y refleja `sv_line_ids`; la edición del volumen está en
«Asignación a SV» (mismo mecanismo; sin saldo paralelo). Sin cambios de negocio: disponibilidad,
reservas, reparto, aplicación y reversa intactos. El volumen documental **no** se recalcula desde
dimensiones.

## 6. Integridad preservada
`processed_lot_id` sigue obligatorio y con `force_save="1"` (fix previo). Elegibilidad de guía,
pertenencia etiqueta–guía, compañía/permisos, límites documentales, idempotencia, atomicidad,
inmutabilidad `applied`, guardar/reabrir, reversa y ausencia de efectos físicos: sin cambios.

## 7. Pruebas y resultados
- Dirigidas `TestSvRebajaMaterial` (MAP/GRAN/SEM/AMT/ARCH): **0 failed, 0 error(s) of 8** (EXIT 0) —
  `logs_rd_tests1.log`.
- Regresión `madenat_lumber_logistics`: **4 failed, 0 error(s) of 342** (EXIT 1) —
  `logs_rd_regression.log`. Fallas = **las mismas 4 preexistentes** (`test_processor_locations.test_09`,
  `test_processor_shipment_ad89.test_t1/t5/t6`).
- Mapeo real guía 19827: **17/17** (comprobación de solo lectura con `odoo shell`).

## 8. Límite de navegador
**No hay navegador** en el entorno: la evidencia es XML/ORM/SQL + pruebas. **V3 *pixel* pendiente**;
la interfaz **no** se declara aceptada. Guion: `docs/GUION_MANUAL_NAVEGADOR.md`.

## 9. Versión y actualización
`odoo --database=madenat_test --update=madenat_lumber_logistics --stop-after-init --no-http
--http-port=8079 --log-level=info` → **EXIT 0** (`logs_rd_update_final.log`). **18.0.1.12.0 →
18.0.1.13.0**. Sin `-u all`; sin despliegue.

## 10. Documentación
`CANON/19` **1.15.0** §19.18; `CANON/02` **12.24.0** §17.16.16; `CANON/03` **6.24.0** §20;
`CANON/05` **8.23.0**; `INDICE` **12.18.0**; `CHANGELOG` `[18.0.1.13.0]`.

## 11. Respaldos y recuperación
`code/modules_pre_18.0.1.12.0.tar.gz` (estado previo reconstruido desde el checkpoint verificado
18.0.1.12.0), `code/modules_post_18.0.1.13.0.tar.gz`, `db/madenat_test_post.dump`,
`db/filestore_post.tar.gz`. Recuperación: extraer tarball previo → `-u madenat_lumber_logistics` →
restaurar dump/filestore. **Nota:** las pruebas son transaccionales (sin datos residuales).

## 12. Propuesta de commit (no ejecutado)
`feat(logistics): rediseña el asistente «Registrar rebaja» con el material del packing list
(CANON/19 §19.18)` — `madenat_lumber_logistics` 18.0.1.13.0 + `tests/test_sv_rebaja_material.py` +
CANON/02/03/05/19/INDICE.
