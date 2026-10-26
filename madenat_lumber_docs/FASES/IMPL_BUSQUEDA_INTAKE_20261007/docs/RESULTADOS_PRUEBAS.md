# RESULTADOS_PRUEBAS — Evidencia de la implementación aislada

## 1. Entorno de prueba (aislado)

| Elemento | Valor |
|---|---|
| Base | `busqintake_iso_20261007` (creada desde plantilla idle `delint_test_20261007`) |
| Servicio | `odoo-18-ce-web:latest`, contenedor one-shot `busqintake_iso` |
| Addons | workcopy `IMPL_BUSQUEDA_INTAKE_20261007/addons` montado **:ro** |
| Módulo | `-u madenat_lumber_intake` (18.0.0.11.0) |
| Aislamiento | `--max-cron-threads=0 --workers=0 --stop-after-init --no-http`, sin SMTP |
| `madenat_test` | **NO tocada** (0 escrituras) |

## 2. Comandos

```bash
cd /home/viruco/dev-stack/odoo/odoo-18-ce/IMPL_BUSQUEDA_INTAKE_20261007
bash run_iso.sh            # clase nueva
# corrida ampliada: se añadieron TestVolumeOfficialVolume, TestIntakeModality,
# TestDocumentalConsole, TestIntakeConsoleActions, TestIntakeNavigationActions
```

## 3. Resultado

| Corrida | Log | Tests | Vítores |
|---|---|---|---|
| Clase nueva (final, 10 pruebas) | `logs/iso_run.log` | 8 (versión 8-tests) | 0 failed, 0 errors |
| Ampliada (nueva + regresión) | `logs/iso_regression.log` | **66** | **0 failed, 0 errors** |

`odoo.tests.result: 0 failed, 0 error(s) of 66 tests` (10 nuevas + 56 de regresión).

## 4. Pruebas nuevas (TestIntakeSearchConsole)

| # | Test | Qué verifica | Vítores |
|---|---|---|---|
| 01 | `test_01_oc_documental_no_se_sustituye_por_la_vinculada` | `oc_documental` = referencia del documento en ambos orígenes; al vincular una OC **no** se sobrescribe el valor mostrado | PASS |
| 02 | `test_02_oc_busqueda_y_agrupacion_coherentes` | búsqueda por `oc_documental`; filtros vinculada/pendiente/no indicada; agrupación por `oc_documental` con grupo real (no vacío) | PASS |
| 03 | `test_03_fecha_significado` | `guide_date_kind` = `emission`/`reception` y `guide_date` correcta por origen | PASS |
| 04 | `test_04_modalidad_tipos` | conteos y agrupación por `ingestion_type` (product/processed/volume) = 3 grupos | PASS |
| 05 | `test_05_producto_real_busqueda` | `product_filter_id` encuentra por **contenido de líneas** en ambos modelos, sin duplicar filas; mezcla de productos → `product_id` común vacío | PASS |
| 06 | `test_06_procesador_por_orden_de_procesamiento` | `processor_id` desde `toll_order_id.processor_id`; **≠** proveedor; agrupa por procesador | PASS |
| 07 | `test_07_incompletos_usuario_operativo_y_navegacion` | registro sin OC/proveedor/procesador no rompe; conteo con **usuario operativo** (no superusuario); navegación al origen | PASS |
| 08 | `test_08_sin_duplicacion_de_filas` | número de filas de la vista = número de orígenes (sin multiplicar por JOIN) | PASS |
| 09 | `test_09_combinacion_modalidad_por_and` | los filtros de modalidad NO son excluyentes: combinados por AND → intersección vacía | PASS |
| 10 | `test_10_lista_muestra_origen_de_fecha` | la lista expone `guide_date_kind` (visible, además del help) | PASS |

## 5. Evidencia SQL (base aislada, solo lectura)

**Columnas de la vista (14 = 11 originales + 3 nuevas; `id`/`source_res_id` intactos):**
```
 id, source_model, source_res_id, ingestion_type, guide_name, guide_date,
 guide_date_kind, partner_id, purchase_id, purchase_reference, oc_documental,
 state, display_reference, processor_id
```

**Significado de fecha por modalidad (`guide_date_kind`):**
```
 ingestion_type | guide_date_kind | count
 processed      | emission        |     7
 product        | emission        |     6   (con guia_fecha)
 product        | reception       |     1   (sin guia_fecha)
 volume         | emission        |     5
```

**OC: la agrupación vieja (purchase_id) habría dado un único grupo vacío; la nueva
(`oc_documental`) discrimina referencias reales:**
```
 tiene_oc_doc | tiene_oc_vinculada | count
 f            | f                  |     3   (OC no indicada)
 t            | f                  |    16   (OC documental, sin vínculo)
-- oc_documental: 14 referencias distintas, longitud máx. 29
-- processor_id no nulo: 0 en la plantilla (las guías no tienen orden toll);
   el test 06 lo cubre con un fixture sintético.
```

## 6. Separación de niveles de verificación

- **V1 Estática (código/XML):** diff mínimo revisado; XML bien formado; el RNG de
  Odoo validó las vistas al cargar (sin errores).
- **V2 ORM/SQL:** ejecutada — 10 pruebas + 56 de regresión + consultas `SELECT`
  de solo lectura sobre la vista.
- **V3 Navegador (UI real):** **NO ejecutada** en esta entrega (pendiente). No se
  llama "UI verificada" a la comprobación de XML/ORM.

## 7. No regresión

Se ejecutaron además las suites existentes que tocan el mismo modelo/vistas, todas verdes:
`TestVolumeOfficialVolume` (proxies OC), `TestIntakeModality`, `TestDocumentalConsole`,
`TestIntakeConsoleActions`, `TestIntakeNavigationActions`.
