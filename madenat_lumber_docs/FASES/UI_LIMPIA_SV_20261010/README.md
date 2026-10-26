# UI_LIMPIA_SV_20261010 — Evidencia (interfaz clara y concisa de «Registrar rebaja»)

**Fecha:** 2026-10-10 · **Entorno:** `madenat_test` / `odoo18_app` (PostgreSQL `odoo18_db`).
**Naturaleza:** expediente de **evidencia**. La doctrina vive en `madenat_lumber_docs/CANON/`
(`19 §19.19`, `02 §17.16.17`, `03 §21`, `05`, `INDICE`).

## 1. Solución
Se aplica el **mismo criterio visual** a las dos pestañas del **mismo asistente** «Registrar rebaja»
(`madenat.sv.imputation.wizard`): «Materiales del retorno» y «Asignación a SV». No se crea otro
wizard/menú/mecanismo. La interfaz anterior fue **rechazada por Mauricio**; esta entrega queda
**pendiente de su aceptación visual**.

## 2. Cabecera única
Se muestra una sola vez: SV de trabajo, guía, **saldo documental del SV**, **seleccionadas**, **con reparto
preparado** y **total preparado para el SV (m³)**. No se repite el nominal ni el saldo completo del SV en
cada fila. Se distingue **seleccionadas ≠ con reparto preparado ≠ total en m³** (no se presenta «N
etiquetas» como N asignaciones válidas si todas siguen en cero).

## 3. Totales y unidades
Piezas de origen; Volumen documental de origen (≠ volumen a imputar); Disponible documental de las
seleccionadas (agregable sin doble conteo porque se calcula por lote); Preparado para el SV. Con varios SV
se separa el **subtotal del SV de trabajo** del **total general**.

## 4. Materiales del retorno
Columnas: Seleccionar · **Etiqueta (limpia)** · SKU origen · Producto · Espesor (mm) · Ancho (mm) ·
Largo (m) · Piezas · Vol. documental (m³) · Disponible (m³) · **A asignar (m³) — EDITABLE**. «A asignar»
se integra con el reparto real (`sv_alloc_ids`): crea/actualiza/elimina SÓLO la fila de esa etiqueta hacia
el SV de trabajo (sin saldo paralelo, sin borrar repartos a otros SV). Subproducto, dimensiones declaradas
y código técnico quedan como columnas **opcionales**.

## 5. Asignación a SV
Un solo SV: **Etiqueta · Medidas · Disponible (m³) · A asignar (m³)**; el SV destino está en la cabecera.
Varios SV: aparece la columna **«SV destino»** (`column_invisible="not wizard_id.multi_sv"`). La
identidad material es la misma en ambas pestañas (etiqueta limpia + medidas «45 × 125 mm · 2,900 m»),
sin cambiar `display_name`.

## 6. Acciones y textos
Botones breves (Seleccionar todas · Quitar selección · **Preparar asignación** · Usar disponible);
«Preparar asignación» aclara «prepara el reparto al SV de trabajo; no aplica la rebaja». «Usar
disponible» tiene el MISMO alcance en ambas pestañas (filas del SV de trabajo de etiquetas seleccionadas) y
**no sobrescribe** cantidades editadas. Footer: Guardar borrador · **Revisar y aplicar** · Cancelar;
Proponer FIFO y Dejar pendiente como `btn-link`. Una ayuda de una línea («Selecciona el material, indica
los m³ y prepara la asignación. Sólo Aplicar registra la rebaja.») y el aviso «Rebaja documental: no mueve
stock físico.».

## 7. Filas sin disponibilidad
`disponibilidad_estado` (Disponible / Aplicado / Reservado / Sin capacidad documental) derivado de los
**saldos reales**; «Seleccionar todas» informa cuántas seleccionadas **no** son asignables
(`not_assignable_line_count` + `no_availability_note`). No se borran reservas ni repartos existentes.

## 8. Evidencia de AMBAS pestañas
- `code/verify_tabs_orm.out`: columnas reales resueltas por el ORM de las **dos** pestañas + cabecera +
  botones (sólo lectura).
- `code/diff_ui_limpia.diff`: diff completo vs **18.0.1.13.0**.
- `logs_tests_ui.log`: suite `TestSvRebajaUiLimpia` (13 casos).
- `logs_regression.log`: regresión del módulo.

## 9. Pruebas y resultados
- Dirigidas `TestSvRebajaUiLimpia` (CAB/EDIT/MED/ETQ/SIN/USE/MULTI/ARCH): **0 failed, 0 error(s) of 13**
  (EXIT 0) — `logs_tests_ui.log`.
- Regresión `madenat_lumber_logistics`: **4 failed, 0 error(s) of 355** (EXIT 1) — `logs_regression.log`.
  Las **4 fallas** son las mismas preexistentes (`test_processor_locations.test_09`,
  `test_processor_shipment_ad89.test_t1/t5/t6`) ⇒ **0 nuevas, 0 errores**.

## 10. Límite de navegador
No hay navegador (Playwright/Selenium/Chromium) en el entorno: la evidencia es XML/ORM + pruebas. La
verificación *pixel* (**V3**) queda **pendiente**; la interfaz **no** se declara aceptada.

## 11. Versión y actualización
`odoo --database=madenat_test --update=madenat_lumber_logistics --stop-after-init --no-http
--http-port=8079 --log-level=info` → **EXIT 0** (`logs_update.log`). Versión
**18.0.1.13.0 → 18.0.1.14.0**. Sin `-u all`; sin despliegue.

## 12. Documentación
`CANON/19` **1.16.0** §19.19; `CANON/02` **12.25.0** §17.16.17; `CANON/03` **6.25.0** §21;
`CANON/05` **8.24.0**; `INDICE` **12.19.0**; `CHANGELOG` `[18.0.1.14.0]`.

## 13. Respaldos y recuperación
`code/modules_post_18.0.1.14.0.tar.gz` (estado post). Estado previo verificable:
`REDISENO_REGISTRAR_REBAJA_20261010/code/modules_post_18.0.1.13.0.tar.gz` (18.0.1.13.0). Recuperación:
extraer el tarball previo → `-u madenat_lumber_logistics`. Las pruebas son **transaccionales** (sin datos
residuales).

## 14. Propuesta de commit (no ejecutado)
`feat(logistics): interfaz clara y concisa de «Registrar rebaja» en ambas pestañas (CANON/19 §19.19)` —
`madenat_lumber_logistics` 18.0.1.14.0 + `tests/test_sv_rebaja_ui_limpia.py` + CANON/02/03/05/19/INDICE.
