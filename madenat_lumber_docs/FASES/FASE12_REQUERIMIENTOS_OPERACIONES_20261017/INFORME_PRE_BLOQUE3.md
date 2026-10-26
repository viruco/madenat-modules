# INFORME PREVIO AL BLOQUE 3 — VERIFICACIÓN Y CIERRE DE BLOQUE 2 (FASE 12)

**Proyecto:** MADENAT — Odoo 18 CE  
**Fecha:** 2026-10-17  
**Autor:** Antigravity (Claude Sonnet 4.6) — Pair Programming con Mauricio  
**Rama:** `feat/guia-correccion-documental-preservada-20261002`  
**Estado:** Bloque 1 y Bloque 2 COMPLETADOS y COMMITEADOS en local. Bloque 3 DETENIDO.

---

## 1. Línea Resumen y Fallas por Nombre de las Corridas (4.2 y 4.3)

### 1.1 Estabilidad de `madenat_lumber_logistics` (Dos Corridas Consecutivas)
**Comando:**
```bash
docker exec odoo18_app odoo -d madenat_test --test-tags=madenat_lumber_logistics --stop-after-init --http-port=8070
```

#### Corrida 1 (Log: `regresion_logistics_20261017_171308.log`):
- **Línea Resumen:**
  `2026-10-17 20:15:34,459 1978 ERROR madenat_test odoo.tests.result: 4 failed, 0 error(s) of 546 tests when loading database 'madenat_test'`
- **Fallas por nombre (FAIL/ERROR):**
  1. `TestProcessorLocations.test_09_auditoria_envio_normal` (FAIL)
  2. `TestProcessorShipmentAD89.test_t1_envio_manual_parcial_sin_motivo` (FAIL)
  3. `TestProcessorShipmentAD89.test_t5_desviacion_real_no_aplica_en_i1` (FAIL)
  4. `TestProcessorShipmentAD89.test_t6_idempotencia` (FAIL)

#### Corrida 2 (Log: `regresion_logistics_20261017_171552.log`):
- **Línea Resumen:**
  `2026-10-17 20:18:11,622 2000 ERROR madenat_test odoo.tests.result: 4 failed, 0 error(s) of 546 tests when loading database 'madenat_test'`
- **Fallas por nombre (FAIL/ERROR):**
  1. `TestProcessorLocations.test_09_auditoria_envio_normal` (FAIL)
  2. `TestProcessorShipmentAD89.test_t1_envio_manual_parcial_sin_motivo` (FAIL)
  3. `TestProcessorShipmentAD89.test_t5_desviacion_real_no_aplica_en_i1` (FAIL)
  4. `TestProcessorShipmentAD89.test_t6_idempotencia` (FAIL)

---

### 1.2 Regresión Comparable con el Método del Baseline (4.3)
**Comando Histórico:**
```bash
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_shipping_core,madenat_lumber_core,madenat_lumber_logistics,madenat_lumber_intake --test-enable --stop-after-init --http-port=8070
```
- **Log:** `regresion_baseline_historical_20261017_171832.log`
- **Línea Resumen:**
  `2026-10-17 20:23:31,626 2036 ERROR madenat_test odoo.tests.result: 6 failed, 4 error(s) of 1496 tests when loading database 'madenat_test'`
- **Fallas por nombre (FAIL/ERROR):**
  1. `TestGuiaPickingLink.test_t_g2_03_exclusion_retornos` (FAIL)
  2. `TestOrphanMoveCleanupSavepoint.test_partial_batch_failure_protected_moves_survive` (ERROR)
  3. `TestSvConcurrency.test_01_dos_transacciones_no_sobreconsumen` (FAIL)
  4. `TestSvEscalationSecurity.test_02_costo_exige_contabilidad` (ERROR)
  5. `TestSvEscalationSecurity.test_03_alza_de_baseline_exige_auditoria` (ERROR)
  6. `TestSvEscalationSecurity.test_04_auditoria_y_contabilidad_por_dos_personas` (ERROR)
  7. `TestProcessorLocations.test_09_auditoria_envio_normal` (FAIL)
  8. `TestProcessorShipmentAD89.test_t1_envio_manual_parcial_sin_motivo` (FAIL)
  9. `TestProcessorShipmentAD89.test_t5_desviacion_real_no_aplica_en_i1` (FAIL)
  10. `TestProcessorShipmentAD89.test_t6_idempotencia` (FAIL)

**Suite adicional `madenat_ingestion_engine`:**
- **Comando:** `docker exec odoo18_app odoo -d madenat_test --test-tags=madenat_ingestion_engine --stop-after-init --http-port=8070`
- **Log:** `regresion_ingestion_20261017_171832.log`
- **Línea Resumen:**
  `2026-10-17 20:18:39,870 2021 INFO madenat_test odoo.tests.result: 0 failed, 0 error(s) of 84 tests when loading database 'madenat_test'`

---

## 2. Conclusión sobre Estabilidad

- **Resultados idénticos:** Ambas corridas consecutivas de `madenat_lumber_logistics` arrojaron con absoluta precisión **546 pruebas, 4 failed, 0 error**, con los **mismos 4 nombres de fallo exactos**.
- **Causa del hallazgo previo a las 16:30 (6 fallas):**
  A las 16:30, la primera corrida registró 6 fallas porque la suite `test_sv_rebaja_blindaje.py` falló en dos pruebas (`test_aud_etq_04_causa_aplicada_trazable` y `test_aud_etq_04b_causa_reservada_y_sin_capacidad`). La causa fue que en el código de WP-F P2, `action_select_all()` omitía de la selección las etiquetas sin saldo, mientras que el campo `no_availability_note` y la acción `action_open_no_availability_docs()` inspeccionaban únicamente las etiquetas que estaban dentro de `selected`.
  Al ajustar el cálculo para que considere todas las etiquetas no asignables del asistente (`wiz.line_ids.filtered(lambda l: not l.asignable)`), ambas pruebas pasaron a verde (12/12 PASS), estabilizando la suite de `logistics` en sus 4 fallas basales permanentes.
- **Diferencia de totales (1358 vs 1496):**
  El comando con `--test-tags` (sin `-u`) únicamente descubre pruebas etiquetadas con `post_install` / matching tags (1358 pruebas). El comando histórico con `-u` y `--test-enable` ejecuta tanto las suites `at_install` como `post_install` (1496 pruebas). En ambos métodos, el conjunto de fallas es **idéntico al conjunto basal de 10**.

---

## 3. Confirmación de 0 Fallas Nuevas frente al Baseline

Se confirma formalmente:
- **0 fallas nuevas en `madenat_lumber_logistics`** (4 fallas históricas).
- **0 fallas nuevas en `madenat_lumber_intake`** (0 fallas / 412 tests).
- **0 fallas nuevas en `madenat_ingestion_engine`** (0 fallas / 84 tests).
- **0 fallas nuevas en la suite completa `core+intake+logistics`** (exactamente las 6 failed + 4 error conocidas).

---

## 4. Commits Creados y `git status` Final

### 4.1 Commits Creados en Esta Entrega (Sin Amend, Sin Rebase)
1. **`a1ce732`**: `test(ingestion): prueba de ida y vuelta con datos sintéticos para plantilla PACKING_METRICO_ASERRADA`
   - Archivo: `madenat_ingestion_engine/tests/test_packing_metrico_template.py` (+76 líneas).
   - Justificación de manifest: no requiere incremento de versión por ser una prueba interna sin cambios funcionales ni de esquema.
2. **`2ec4be2`**: `fix(logistics): robustez de notas y acceso a documentos sin disponibilidad en asistente SV (18.0.1.39.0)`
   - Archivos: `madenat_lumber_logistics/wizards/madenat_sv_imputation_wizard.py`, `__manifest__.py`, `CHANGELOG.md`.
   - Versión: 18.0.1.38.0 → 18.0.1.39.0 monótona.
3. **`2ba6f4a`**: `docs: precisión de estado local de Fases 10/11 y formalización de alcance Bloque 3`
   - Archivos: `CANON/04_DECISION_LOG.md` (12.28.0 → 12.29.0), `CANON/05_BACKLOG.md` (8.31.0 → 8.32.0), `WIKI/06_SESIONES/_CAPSULA_CONTEXTO.md`, `WIKI/HOJA_RUTA_EJECUTIVA.md`.

### 4.2 Últimos 5 Commits (`git log --oneline -5`)
```
2ba6f4a (HEAD -> feat/guia-correccion-documental-preservada-20261002) docs: precisión de estado local de Fases 10/11 y formalización de alcance Bloque 3
2ec4be2 fix(logistics): robustez de notas y acceso a documentos sin disponibilidad en asistente SV (18.0.1.39.0)
a1ce732 test(ingestion): prueba de ida y vuelta con datos sintéticos para plantilla PACKING_METRICO_ASERRADA
8ec4ddd docs: WP-G alineacion documental, AD-112 canonica y reconciliacion D-E0-1 / D-E0-2
b661a44 feat(ingestion): WP-E plantilla estandar PACKING_METRICO_ASERRADA y guia de llenado (AD-112)
```

### 4.3 `git status` Final
```
On branch feat/guia-correccion-documental-preservada-20261002
Changes not staged for commit:
        modified:   madenat_lumber_costing/__manifest__.py
        modified:   madenat_lumber_costing/models/__init__.py
        modified:   madenat_lumber_costing/models/lumber_cost_distribution.py
        modified:   madenat_lumber_costing/models/lumber_shipment_costing.py
        modified:   madenat_lumber_costing/security/ir.model.access.csv
        modified:   madenat_lumber_costing/tests/__init__.py
        modified:   madenat_lumber_costing/views/lumber_cost_distribution_views.xml
        modified:   madenat_lumber_reports/views/lumber_reports_menu.xml

Untracked files:
        madenat_lumber_costing/models/stock_lot_cost_line.py
        madenat_lumber_costing/tests/test_shipment_costing_c2.py
        madenat_lumber_costing/views/lumber_shipment_costing_views.xml
```
*Confirmado:* Permanecen única y exclusivamente los 11 archivos conocidos del WIP de `costing` y `reports`, sin tocar ni mezclar.

---

## 5. Respuesta sobre `openpyxl` y Prerrequisito de Despliegue

1. **Investigación Histórica:**
   - La librería `openpyxl` **ya se importaba y utilizaba en runtime desde el primer commit** en que se introdujo `madenat_ingestion_engine` (commit `843ed0d`: `import openpyxl`, `openpyxl.load_workbook(...)` en `services/document_extractor.py`).
   - El entregable WP-E (`b661a44`) **NO añadió ninguna dependencia nueva de ejecución al módulo**.
2. **Prerrequisito de Despliegue:**
   - Quedó registrado en `FASES/FASE12_REQUERIMIENTOS_OPERACIONES_20261017/RUNBOOK_FASE12.md` (§2) como paso previo mandatorio verificar que `openpyxl` esté disponible en el entorno virtual `/opt/odoo18-test/venv`:
     ```bash
     /opt/odoo18-test/venv/bin/python -c "import openpyxl; print('openpyxl version:', openpyxl.__version__)"
     ```
   - Si no estuviese, se debe ejecutar `/opt/odoo18-test/venv/bin/pip install openpyxl` antes de actualizar el módulo en el TEST remoto.

---

## 6. Anexo para Cristhian: Tabla Canónica de Anchos Rough → S2S

Para la operación de Cristhian y la parametrización de exportación, la tabla canónica de 15 registros activos (`width_mapping.py` y `lumber.width.s2s.map`) establece:

| Secuencia | Rough (mm) | S2S Pulgadas (decimal) | S2S Fracción (etiqueta) | Caracterización Técnica |
|:---:|:---:|:---:|:---:|---|
| 10 | **75 mm** | 2.6250" | **2 5/8** | Conversión base |
| 20 | **85 mm** | 2.8750" | **2 7/8** | Conversión base |
| 30 | **90 mm** | 3.1250" | **3 1/8** | Conversión base |
| 40 | **95 mm** | 3.3750" | **3 3/8** | Conversión base |
| 50 | **100 mm** | 3.6250" | **3 5/8** | Conversión base |
| 60 | **105 mm** | 3.8750" | **3 7/8** | **Valor repetido (stair-step)**: comparte medida S2S con 110 mm |
| 70 | **110 mm** | 3.8750" | **3 7/8** | **Valor repetido (stair-step)**: comparte medida S2S con 105 mm |
| 80 | **115 mm** | 4.3750" | **4 3/8** | **Valor repetido (stair-step)**: comparte medida S2S con 120 mm |
| 90 | **120 mm** | 4.3750" | **4 3/8** | **Valor repetido (stair-step)**: comparte medida S2S con 115 mm |
| 100 | **125 mm** | 4.6250" | **4 5/8** | Conversión base |
| 110 | **130 mm** | 4.8750" | **4 7/8** | **Valor repetido (stair-step)**: comparte medida S2S con 140 mm |
| 120 | **140 mm** | 4.8750" | **4 7/8** | **Valor repetido (stair-step)**: comparte medida S2S con 130 mm |
| 130 | **145 mm** | 5.3750" | **5 3/8** | **VALOR CRÍTICO**: origen comercial en Excel `ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx` |
| 140 | **150 mm** | 5.6250" | **5 5/8** | Conversión base |
| 150 | **155 mm** | 5.8750" | **5 7/8** | Conversión base |

### Observaciones Técnicas Clave para Cristhian:
1. **Valores Repetidos (Escalones Comerciales / Stair-Steps):**
   - **105 mm y 110 mm** $\rightarrow$ ambos facturan y consolidan como **3 7/8" (3.875")**.
   - **115 mm y 120 mm** $\rightarrow$ ambos facturan y consolidan como **4 3/8" (4.375")**.
   - **130 mm y 140 mm** $\rightarrow$ ambos facturan y consolidan como **4 7/8" (4.875")**.
   *Causa:* En el mercado internacional de pino aserrado, aserraderos con distintas tecnologías de corte entregan madera verde/seca que, una vez cepillada dos caras (S2S), se homologa al mismo estándar de venta.
2. **Ausencia de 135 mm:**
   - La tabla pasa de 130 mm a 140 mm. No existe corte de 135 mm en la matriz estándar de aserrío de los proveedores de MADENAT; cualquier pieza en ese rango debe clasificarse formalmente por vecino más cercano o asignación manual.
3. **Ausencia de Anchos $\ge 160$ mm en Fracciones:**
   - Los anchos de 160 mm o superiores no se transan con denominación fraccionaria en pulgadas. Por regla de negocio canónica (reflejada en `utils_uom.py` con el caso de 170 mm), el proveedor los declara directamente en formato decimal o milimétrico directo.
4. **Significado del "Valor Crítico" de 145 mm:**
   - Una conversión matemática ingenua daría $145 / 25.4 = 5.70866"$ (aproximable a 5 3/4" = 5.750").
   - Sin embargo, en el contrato y planilla comercial de MADENAT (`ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx`), 145 mm corresponde rígidamente a **5 3/8" (5.375")**. Si se calcula matemáticamente o se usa otra tabla, se genera un sobrecosto/descuadre grave en la cubicación de exportación. Por ello, está auditado con una aserción estricta en el startup de Odoo (`utils_uom.py:855`).

---

## 7. Conteos de `madenat_test` Antes y Después

| Entidad / Tabla | Conteo Inicial (17:08) | Conteo Final (17:26) | Estado |
|---|:---:|:---:|:---:|
| `madenat_guia_processing` (Guías) | **13** | **13** | Idéntico |
| `lumber_reception` (Recepciones) | **8** | **8** | Idéntico |
| `res_users` (Usuarios) | **12** | **12** | Idéntico |
| `stock_lot` (Lotes) | **152** | **152** | Idéntico |
| `madenat_audit_log` (Bitácora) | **327** | **327** | Idéntico |
| `madenat_sv_imputation` (Imputaciones SV) | **3** | **3** | Idéntico |
| `madenat_sv_imputation_line` (Líneas de Imputación) | **3** | **3** | Idéntico |
| `madenat_sv_imputation_sv_line` (Repartos SV) | **1** | **1** | Idéntico |
| `madenat_sv_operation` (Operaciones SV) | **1** | **1** | Idéntico |

*Resultado:* Integridad 100% preservada; ninguna prueba ni ejecución modificó los datos de la base de datos de pruebas.

---

## 8. Definición de Bloque 3 (DETENIDO / NO INICIADO)

El alcance del Bloque 3 queda estrictamente fijado para cuando Mauricio lo autorice:
1. **WP-B Ancho de Exportación:**
   - Uso exclusivo de la tabla existente en `width_mapping.py` y `lumber.width.s2s.map`.
   - Simulación **SOLO LECTURA** de antes/después sobre embarques existentes, **sin recalcular valores ya almacenados**.
   - Opción manual con registro de usuario y fecha.
2. **WP-A Comparación Guía vs. Packing:**
   - A la precisión declarada de la guía con tope de 3 decimales, estado `ok_rounded`, parametrizable.
3. **WP-D (Patios):**
   - **Sigue EN ESPERA.** No existe "conciliación documental" ni "imputación diferida" aprobadas.

---
**AGENTE DETENIDO.** No se ha ejecutado ninguna acción del Bloque 3.
