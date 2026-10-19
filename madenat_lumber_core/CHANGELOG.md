## [18.0.6.22.0] - 2026-10-19

### Added
- **Bloque 6 (AD-127) — Patios por Tipo, Inventario por Patio, Etiquetas y Packing Estándar**:
  - **6A (Patios por tipo)**: Campo `patio_type` (`service`, `port`) en `stock.location` con resolución por datos y asignación automática por origen sin bloqueo. Aplicación autorizada en `madenat_test` (MARVAL como puerto, Ferramenta como servicio). Bodega Tepornac y Puerto Coronel sin tocar.
  - **6B (Visibilidad e inventario por patio)**: Filtros y búsqueda por patio en Consola de Ingresos; menú "Inventario por Patio" con lista y pivote readonly sobre `stock.quant` usando volumen nominal de compra.
  - **6C (Etiquetas de volumen)**: Normalización de etiquetas a "Vol. Compra (m³)" y "Vol. Export (m³)" en pantallas de ingreso, packing y lotes, con volumen de compra visible por etiqueta.
  - **6D (Packing estándar)**: Formato registrado en `lumber.ingestion.format` con `noupdate="1"`.

## [18.0.6.21.0] - 2026-10-18

### Added
- **Bloque 5D (AD-126) — Reconciliación y Claridad del Real Físico**:
  - **Campo physical_status**: Campo calculado de estado (`calculado`, `sin_mapeo`, `no_aplica`) en `madenat_guia_processing_line` y `stock.lot`.
  - **Prevención de % con Ceros**: Métrica `% Dif.Vol` (`vol_diff_pct`) queda vacía (`False`) cuando `physical_status != 'calculado'`, evitando divisiones anómalas o falsas alertas del -100%.
  - **Vistas comparativas 5D**: Incorporación de badge de estado y filtros guardados dedicados por estado físico (`filter_physical_calculado`, `filter_physical_sin_mapeo`, `filter_physical_no_aplica`).
  - **Matriz de Ingesta CANON/12 §3.3**: Formalización documental de todos los flujos de ingesta (guías A-D, recepción volumen, consolidación administrativa, procesados/maquila, blanks F6 y métrico). Test suite: `TestVolumeComparison5C.test_05` (5 tests PASS, total 14 tests Bloque 5).

## [18.0.6.20.0] - 2026-10-18

### Added
- **Bloque 5 (AD-126) — Volumen Real Físico y Comparativo de los Tres Volúmenes**:
  - **5A (Modelo lumber.thickness.real.map)**: Nuevo modelo persistente con seguimiento chatter (`mail.thread`), validación de coherencia ($\le 0.001"$), unicidad por espesor visual activo, datos semilla con `noupdate="1"` (4/4 a 8/4) y getter `get_thickness_real_mm` en `madenat.ingestion.config` sin copias en código (D6). Test suite: `TestLumberThicknessRealMap5A` (4 tests PASS).
  - **5B (Campo vol_physical_real_m3 F3)**: Campo nuevo `vol_physical_real_m3` (digits 16, 3) en `madenat_guia_processing_line` y `stock.lot`. Cálculo canónico F3: espesor real (mm de 5A) $\times$ ancho nominal (mm) $\times$ largo (m) $\times$ piezas / 1.000.000 con redondeo único `r3()`. Blanks directo a stock y perfiles métricos no aplicables quedan en 0.000. Invarianza total de históricos. Test suite: `TestVolPhysicalReal5B` (5 tests PASS).
  - **5C (Comparativo de los Tres Volúmenes)**: Vitas de lista (`list`) y pivote (`pivot`) de solo lectura (`create="false" edit="false" delete="false"`) comparativas de Compra Nominal, Real Físico, Exportación Embarque y columna `% Dif.Vol` (`vol_diff_pct`), con alerta condicional en rojo (`decoration-danger="is_export_greater_nominal"`) ante anomalías donde exportación supera al nominal de compra. Menú operativo bajo Control de Lotes con permisos para Operaciones, Auditoría y Contabilidad. Test suite: `TestVolumeComparison5C` (4 tests PASS).

## [18.0.6.19.0] - 2026-10-18

### Changed
- **Bloque 4M (AD-125) — Cierre de Arnés de Pruebas y Diagnóstico de Configuración**:
  - **M1 (Regla canónica de regresión con -u)**: Prohibición estricta de flag `-i` en arnés de pruebas sobre bases existentes según `loading.py:199` y `convert.py:347`. Nuevo script canónico con `-u` y registro en `CANON/03_TESTS.md` §31.
  - **M2 (Diagnóstico noupdate y mejora de test_12)**: Análisis del flag `noupdate` en `ir_model_data` y limitación estructural en Odoo `_update_xmlids`. Mejora de `test_12` en `test_export_width_s2s_wpb.py` auditando presencia en BD y flags.
  - **M3 (Rectificación oficial de decisión D1)**: Registro de sobreescritura de `madenat.out_of_table_behavior` de `'direct'` a `'warning'` en regresión 4K con `-i`. Mantenido en `'warning'` sin alteración manual (D1).
  - **M4 (Erradicación de literal 2.36)**: Reemplazo de `Decimal('2.36')` por constante del sistema `MBF_TO_M3` en `test_visual_dimension_l3.py:test_05`.

## [18.0.6.18.0] - 2026-10-18

### Changed
- **Bloque 4L (AD-124) — Cierre Definitivo del Bloque 4**:
  - **L1 (Diagnóstico de parámetro XML)**: Identificada sobreescritura de `madenat.out_of_table_behavior` por recarga XML en ejecución previa con `-i` debido a `noupdate=False` en `ir_model_data`. Parámetro mantenido en `'warning'` sin alteración manual (D1).
  - **L2 (Verificación dimensional canónica)**: Rectificadas condiciones de cálculo de anchos a 100 pzas, 1.5", 4.0 m. Esclarecido factor 0.8 como largo de paquete exploratorio previo de 3.20 m (10.5 ft). Coincidencia exacta con volúmenes de exportación esperados.
  - **L3 (Resolución visual basada en datos)**: Modificado `madenat_guia_processing.py` para resolver dimensión visual directamente contra `lumber.width.s2s.map` activo. 150 mm resuelve a `'5 5/8'` (eliminando asimetría de exportación); anchos fuera de tabla resuelven a formato métrico `{mm}mm`. Erradicada la función deprecada `get_s2s_exclusion_widths()` y lista residual de `madenat_ingestion_config.py`. Nueva suite TDD `TestVisualDimensionL3` (5 tests PASS).
  - **L4 (Precisión de constante 1550)**: Corrección de la diferencia relativa entre 1550.003096 y 1550.003 a $6.19 \times 10^{-8}$ ($0.0000062\%$).
- **Bloque 4J (AD-122) — Cierre Definitivo del Bloque 4**:
  - **J1 (Eliminación de copia estática S2S)**: Retirada de `S2S_WIDTH_LOOKUP` de `utils_uom.py:658-675` y `S2S_WIDTH_MAP` de `simulacion_solo_lectura_remoto.py:22-38`. Consulta delegada al modelo ORM `lumber.width.s2s.map`. Ampliada prueba anti-copia `test_16` para escanear todo el código productivo `madenat_*`.
  - **J2 (Prevención de doble redondeo en volúmenes y MBF)**: Unificación a redondeo único `r3()` sobre el valor final sin truncamientos intermedios a 4 decimales en `madenat_guia_processing.py:4088`, `stock_lot.py:1243, 1262` y `lumber_reception.py:827`. Nueva suite TDD `test_double_rounding_j2.py` (4 tests PASS).
  - **J3 (Regresión final completa)**: 1.544 pruebas (1.540 base + 2 health check + 4 double rounding), 0 fallas nuevas, 10 fallas históricas conocidas estables.
  - **J4 (Auditoría de ubicaciones de patio)**: Ratificación de IDs reales en `madenat_test` (17 PUERTO CORONEL, 18 MARVAL, 19 Bodega Tepornac), regla R3 sin IDs en código.
  - **J5 (Verificación de modelos y reglas)**: Verificada existencia en BD de `lumber.blank.nominal.map`, `lumber.thickness.visual.rule` y parámetros. Ratificada vigencia de `LUMBER_DIMENSION_MAP` y `get_s2s_exclusion_widths` en código productivo.
  - **J6 (Documentación canónica)**: CANON/02 (§18.1 como ejemplo ilustrativo D4), CANON/04 (AD-122), CANON/05 (TD-122), CANON/17 (§9.4), e INDICE_DOCUMENTACION sincronizados monótonamente.

## [18.0.6.17.0] - 2026-10-18

### Changed
- **Bloque 4H (AD-121) — Coherencia Exacta S2S y Verificación de Línea Base (H1–H6)**:
  - **H3 (Coherencia exacta decimal/etiqueta S2S con TDD)**:
    - Ajustada la tolerancia máxima de divergencia entre `s2s_decimal` y `s2s_label` en `lumber.width.s2s.map` de $\pm 1/16"$ ($0.0625$) a $\le 0.001"$ (coherencia exacta).
    - Suite de pruebas unitarias actualizada con casos TDD: 4.125 falla, 4.4375 falla, 4.375 pasa.
  - **H1 (Línea base stock_lot fijada)**:
    - Fijación de la línea base canónica única de `stock_lot` en `6667a4bd9f3aeff24a8588d32da23ed2` auditada al 2026-10-18, respaldada por la invariancia 100% de Consulta B (`5c2152...`), A.1 (`9e9196...`) y A.2 (`6b1ec7...`).
  - **H2 (Regresión baseline 1.536 pruebas)**:
    - Conservación estricta de las 10 fallas históricas conocidas (6 en core, 4 en logistics; 0 en intake/shipping_core). Cero fallas nuevas.
  - **H6 (Regla de 3 decimales verificada)**:
    - Verificado por SQL que 100% de los registros almacenados tienen exactamente $\le 3$ decimales en volúmenes.

## [18.0.6.16.0] - 2026-10-18

### Added
- **Bloque 4G (AD-120) — Cierre Técnico Final en Desarrollo (Sin Push Ni Despliegue)**:
  - **G1 (Retiro de copias hardcode)**:
    - Retirada la constante a nivel de clase `_BLANKS_NOMINAL_MAP` y `_NOMINAL_TOLERANCE` de `reception_parser.py`. Delega canónicamente en `madenat.ingestion.config.get_blank_nominal_map()`.
  - **G3 (Script pre_deploy_health_check.py reescrito con 3 niveles)**:
    - Niveles OK, ADVERTENCIA (código 0, detecta `out_of_table_behavior = 'direct'` y patios `is_patio = False` según D1/D2) y CRÍTICO (código 1).
    - Verificación de versiones de todos los módulos MADENAT (incluidos intake y shipping_core) y tabla de 15 anchos de Cristhian. Modo solo lectura con rollback forzado.
  - **G5 (UserError de tabla S2S vacía acotado a perfiles imperiales)**:
    - El `UserError` por tabla vacía en `madenat_ingestion_config.py` queda acotado exclusivamente a las rutas dependientes de la tabla S2S (perfiles imperiales con ancho < 170 mm).
    - Perfiles métricos y anchos directos (>= 170 mm) no se interrumpen aunque la tabla esté vacía.
  - **G7 (Script de simulación de embarques solo lectura remoto)**:
    - Incorporado `scripts/simulacion_embarques_solo_lectura_remoto.py` (estrictamente de solo lectura, sin operaciones de escritura ni commit).
  - **G8 (Tabla S2S: edición por interfaz con trazabilidad y coherencia)**:
    - Modelo `lumber.width.s2s.map` con tracking de campos (`mail.thread`) para auditoría de cambios (usuario, fecha, valores).
    - Constraint de coherencia `_check_decimal_label_coherence` entre `s2s_decimal` y `s2s_label` (tolerancia máxima ±1/16" = 0.0625).
    - Permisos de edición otorgados a `group_lumber_config_manager` y `group_madenat_auditoria`; lectura para usuarios base.
    - Preservación estricta de registros históricos (R5/D6): editar un ancho en la tabla solo afecta cálculos nuevos.
    - Suite de pruebas unitarias dedicada `test_lumber_width_s2s_map_g8.py` (4/4 pasando).

## [18.0.6.15.0] - 2026-10-18

### Added
- **Bloque 4F (AD-119) — Cierre Técnico Previo al Despliegue (Sin Datos Históricos)**:
  - **F1 (Tabla S2S sin copia en código)**:
    - Eliminado el diccionario estático de respaldo en `madenat_ingestion_config.py` (incluyendo la entrada errónea legacy `115: (4.125, "4 1/8")`).
    - Única fuente de verdad: `lumber.width.s2s.map`. Si no existen registros activos, falla controladamente con `UserError` y log estructurado.
    - Pruebas unitarias: tabla vacía lanza `UserError`, 115 mm resuelve a 4.375 + sobreancho = 4.500", y verificación por introspección de ausencia de diccionario estático en código.
  - **F2 (Blanks y retiro limpio de deduction_factor)**:
    - Probado vector canónico 16 ft × 250 = 4,425 m³ y 16 ft × 270 = 4,778 m³ con registro real `f5085` de BD (`madenat_test`).
    - Retirado el campo `deduction_factor` del modelo `lumber.export.formula` y de las vistas XML sin alterar ni eliminar la columna en la base de datos PostgreSQL.
    - Casos con volumen documental declarado (`vol_documental_m3`) conservados íntegros sin recálculo.
  - **F3 (Constante única de 1550)**:
    - Unificada la constante física a `CONST_M3_TO_IN2_M = Decimal('1550.003')` en `utils_uom.py`, manteniendo `INCH_SQ_METERS_TO_M3` como alias directo para compatibilidad integral.
    - Comprobación matemática: cero diferencias de volumen a 3 decimales en los 15 anchos, Guía 26270 y casos JCE.
  - **F7 (Script de comprobación previa al despliegue)**:
    - Implementado `madenat_lumber_core/scripts/pre_deploy_health_check.py` (solo lectura, rollback garantizado, código de salida 1 ante discrepancias).
    - Valida 15 anchos activos, parámetros `madenat.*`, módulos instalados, ausencia de recálculo histórico, y consistencia de patios/ubicaciones.

## [18.0.6.14.0] - 2026-10-18

### Added
- **Bloque 4E (AD-118) — Ajustes Finales de Ingesta, Parámetros y Resolución Documental**:
  - **E1 (Parametrización umbral ancho directo y comportamiento fuera de tabla)**:
    - Eliminado literal `155 < rough_mm < 170` en `madenat_ingestion_config.py`.
    - Parámetro `madenat.direct_width_min_mm` (170.0) y `madenat.out_of_table_behavior` ('warning').
    - Regla unificada: ancho en tabla S2S activa -> S2S + sobreancho; ancho ausente y menor a 170 mm -> comportamiento configurado ('warning' emite advertencia en log y chatter de guía y aplica mm/25.4; 'block' lanza `ValidationError`; 'direct' aplica mm/25.4 directo); ancho ausente >= 170 mm -> mm/25.4 directo sin advertencia. Cubre todos los huecos (<75, 80, 115, 135, 165).
  - **E2 (Valores por defecto en DATA con noupdate="1")**:
    - Declarados en `data/ingestion_config.xml`: `param_s2s_overwidth_inches` (0.125), `param_out_of_table_behavior` ('warning'), `param_direct_width_min_mm` (170.0), rangos de secado (`param_drying_temp_min_c`, `param_drying_temp_max_c`, `param_drying_duration_min_hours`, `param_drying_duration_max_hours`).
  - **E3 (Sincronización 15 anchos activos S2S)**:
    - Revertido `active=False` de `seed_s2s_115` en `data/ingestion_seed_fase2.xml` e incluido 115 mm en fallback de python. Tanto base limpia como `madenat_test` poseen exactamente 15 anchos activos (75 a 155 mm).
  - **E4 (Resolución de ancho sin heurística con señal explícita is_s2s_inches)**:
    - Reemplazada la tolerancia numérica por parámetro explícito `is_s2s_inches` en `get_s2s_adjustment()` y `resolve_export_width()`.
    - Orden canónico de 4 ramas: 1) Manual (`export_width_manual_inches`), 2) Tabla S2S activa, 3) Documental en pulgadas S2S (`is_s2s_inches=True`, ej. JCE 5 3/8" x 16' = 4,997 m³), 4) Directo (mm/25.4) con umbral paramétrico 170 mm.

## [18.0.6.13.0] - 2026-10-17

### Added
- **Bloque 4 (AD-116 / AD-117) — Regla de Ancho por Datos, Blanks F4/F6, Gestión de Patios y Secado en Horno**:
  - **Bloque 4A (F2/F5 — Regla de ancho por datos)**: Regla de ancho decidida exclusivamente por datos en `lumber.width.s2s.map` (14 anchos activos de la planilla de Cristhian, 75 a 155 mm) + sobreancho configurable (`madenat.s2s_overwidth_inches`, 0,125" por defecto). Anchos ausentes de tabla utilizan `mm / 25.4` directo. Parámetro `madenat.out_of_table_behavior` ('direct', 'warning', 'block') para el rango de transición 155-170 mm. Parámetro obsoleto `madenat.s2s_exclusion_widths` deprecado. Prevalencia de ancho manual (`export_width_manual_inches` con motivo obligatorio y chatter) preservada.
  - **Bloque 4B (F4/F6 — Blanks)**: Eliminada deducción de 1/16" en `lumber.export.formula` (`deduction_factor = 0.0`) y en `lumber.reception`. En Blanks que pasan directo a stock se conserva el volumen documental declarado (`vol_documental_m3`) sin recálculo. Vectores canónicos F4 validados: 16 ft × 250 = 4,425 m³; 16 ft × 270 = 4,778 m³ (espesor 6/4 = 1,5", ancho 3 5/8 + 1/8 = 3,75").
  - **Bloque 4C (F7 — Patios)**: Marcador `is_patio` en `stock.location` indexado. Acción y menú para gestión de patios en inventario. Filtros y agrupadores por patio y por orden de compra en la consola de recepción. Seed con `noupdate="1"` para Patio Ferramenta. Separación estricta entre patio (`stock.location`) y procesador (`res.partner`). Cero IDs o nombres hardcodeados (regla H2).
  - **Bloque 4D-1 (F6 — Secado en Horno)**: Campos opcionales en `stock.lot`: `drying_temp_c`, `drying_duration_hours`, `drying_date`. Constraint de validación que lee rangos dinámicamente desde `madenat.ingestion.config` (`get_drying_temp_range()` [50-90 °C] y `get_drying_duration_range()` [50-80 h]), sin literales en el código. Vista y pestaña de secado en form de lote. Cero recálculo sobre lotes históricos.
  - **Commit 0a89536 (Fix get_s2s_adjustment)**: Soporte en `get_s2s_adjustment()` para dimensiones documentales expresadas en pulgadas S2S normalizadas a mm (ej: 5 3/8" = 136,525 mm en Notas de Venta JCE), asegurando compatibilidad sin duplicar el sobreancho.

## [18.0.6.12.0] - 2026-10-17

### Fixed
- **WP-B / AD-115 — Restablecimiento de cálculo automático de volumen de embarque y preservación de opción manual**:
  - En `MadenatGuiaProcessingLine._compute_vol_shipment_m3` y `StockLotExtended._compute_vol_shipment_m3`, se restablece el cálculo automático preexistente a 036cc9b (`width_calc = a_in + float(recargo)` con `recargo = get_s2s_adjustment(self.env, line.ancho_mm)`).
  - Causa raíz de la auditoría: La tabla neta S2S introducida en 036cc9b generaba una reducción de -1,386 m³ (-2,89%) en las 17 líneas de la Guía 26270 (46,623 m³ vs 48,009 m³ almacenados y considerados correctos por operaciones). Para 150 mm, el histórico almacenado utilizaba conversión métrica directa (150/25.4 = 5.9055") por encontrarse 150 mm en la lista de exclusiones de recargo (`[150.0, 160.0, 170.0, 180.0, 200.0]`).
  - Prevalencia de ancho manual: Si el operador define `export_width_manual_inches` (>0 con motivo obligatorio), este prevalece sobre el cálculo automático.
  - Suite de pruebas adaptada: `tests/test_export_width_s2s_wpb.py` adaptada a 7 tests PASS, incluyendo test de regresión con líneas sintéticas de la Guía 26270.

## [18.0.6.11.0] - 2026-10-17

### Added
- **WP-A (FASE 12) — Regla de equivalencia Guía vs Packing ('ok_rounded')**:
  - Regla canónica: `d` = decimales declarados de la guía (tope configurable mediante `ir.config_parameter` `madenat.guia_packing_max_decimal_places`, por defecto 3).
  - La guía y el packing son equivalentes si `round(packing, d) == round(guía, d)`.
  - Nuevo estado `'ok_rounded'` ("Consistente por redondeo") en `documental_conciliation_state`.
  - Cuando son equivalentes, el volumen del Packing es el valor operativo (`volume_operational_m3 = round(packing, 3)`).
  - Guía sin packing genera estado `'partial'`.
  - Soporte de precisión extendida a 6 decimales en `packing_volume_declared_m3` para resguardar valores reales como 57,839556 m³.
  - Suite de pruebas unitarias: `tests/test_guia_packing_equivalence_wpa.py` (6 tests PASS).

## [18.0.6.10.0] - 2026-10-17

### Added
- **WP-B (FASE 12) — Ancho de exportación canónico y opción manual**:
  - `MadenatGuiaProcessingLine._compute_vol_shipment_m3` y `StockLotExtended._compute_vol_shipment_m3`: aplican la tabla canónica Rough -> S2S (`width_mapping.py` y `lumber.width.s2s.map`) para anchos entre 75 y 155 mm (excluyendo 135 mm).
  - Fuera del rango de la tabla (< 75 mm o > 155 mm) y para 135 mm: mantiene la división directa métrica por 25.4.
  - Campos de asignación manual en `madenat.guia.processing.line`: `export_width_manual_inches`, `export_width_manual_user_id`, `export_width_manual_date`, `export_width_manual_reason`.
  - Motivo obligatorio: `_check_export_width_manual_reason` lanza `ValidationError` si se asigna ancho manual sin motivo.
  - Trazabilidad y bitácora: la asignación de ancho manual registra usuario, fecha, motivo y valor en el chatter (`processing_id.message_post`).
  - No altera valores almacenados preexistentes (aplica en creación o edición).
  - Suite de pruebas: `tests/test_export_width_s2s_wpb.py` (6 tests PASS).

## [18.0.6.9.0] - 2026-10-12

### Added
- **H3 / H-SEC-5 (FASE 4) — La bitácora `madenat.audit.log` es APPEND-ONLY.** `write()` y `unlink()` lanzan un
  `UserError` de **negocio** —incluso con `sudo()` y para el grupo de sistema— mediante
  `_audit_mutation_allowed()`: única excepción **test-only** = token VIVO `madenat_sv_test_cleanup_token` +
  entorno estricto (`--test-enable` real + BD de test). Un token arbitrario NO habilita nada.
  **LÍMITE HONESTO:** no impide `UPDATE`/`DELETE` por **SQL directo** ni por un **administrador de base de
  datos**; la defensa adicional (trigger de BD o hash encadenado) queda **propuesta y NO implementada**.
  Las correcciones se registran siempre como **eventos NUEVOS**, nunca editando.
- **H2 (FASE 4) — Rol autorizado para eliminar guías.** `GUIA_DELETE_GROUPS` + `_guia_delete_group_ok()`
  (jefatura de operaciones **o** grupo de sistema) sustituyen la exigencia del grupo técnico
  `stock.group_stock_manager` en `unlink()` y en `_cleanup_orphan_moves_guia()`. No se amplían permisos de
  stock ni se crean grupos.
- Suite `tests/test_audit_log_immutability.py` (H3: bloqueo de `write`/`unlink`, ACL y bypass test-only).

### Changed
- **H1 (FASE 4) — Motivo OBLIGATORIO en la vía directa.** Se elimina el valor por defecto («sin motivo
  declarado») de la FASE 3: sin `madenat_guia_delete_reason` no vacío el `unlink()` **se bloquea** con un
  `UserError` que guía al asistente. La eliminación nativa de la interfaz (lista/formulario) queda por tanto
  **bloqueada con mensaje**, sin modificar botones ni vistas.
- ACL `access_madenat_audit_log_manager`: **retirados `write` y `unlink`** a `base.group_system`
  (`1,1,1,1` → `1,0,1,0`); `create`/`read` se conservan.
- `test_guia_processing.test_06` pasa motivo explícito (dependía del valor por defecto retirado).

### Fixed
- **H3 — limpieza test-only del ledger** (`madenat_sv_internal._sv_test_cleanup_token`): el borrado de la
  bitácora aporta el token de limpieza (mismo patrón inerte), imprescindible tras activar la inmutabilidad.

## [18.0.6.8.0] - 2026-10-12

### Added
- **G1 (FASE 3) — Guardas de eliminación de `madenat.guia.processing` (D-G1..D-G3).** Nueva guarda **central y única**
  en `unlink()`, reutilizada por la vía directa y por el asistente (sin duplicar lógica):
  - **Pre-chequeo de dependencias (`_guia_deletion_blockers`)**: bloquea si algún lote de la guía tiene
    `stock.quant`, `stock.move.line`, líneas de coste, o si hay lotes SV de volumen (`volume_source_guia_id`),
    albaranes vinculados, operaciones SV, imputaciones SV o relaciones envío–retorno. **Mensaje de NEGOCIO** en
    español (D-G2) con el nombre de la guía, el motivo concreto y **alternativas** (anular/corregir/revertir);
    **nunca** un error técnico de clave foránea.
  - **Motivo + bitácora (D-G3)**: registra en `madenat.audit.log` (`action_type='guia_delete_permanent'`) el
    usuario/motivo/estado antes de eliminar; si el registro falla, se aborta. Motivo desde el contexto
    (`madenat_guia_delete_reason`); la vía directa usa un motivo por defecto documentado
    («sin motivo declarado») para no romper la compatibilidad.
  - **Borrado controlado de lotes vacíos**: los lotes vinculados **sin** existencias/movimientos/SV/coste se
    eliminan junto con la guía ⇒ **no quedan lotes huérfanos** (comportamiento elegido y documentado).
  - Se mantienen intactas las guardas por **estado** (solo `draft`/`cancelled`) y el **bypass test-only**
    (marcador + `--test-enable`).
- Contexto interno `madenat_guia_delete_logged` para que el asistente (que ya audita con snapshot) **no duplique**
  la bitácora.

### Notes
- **Local** (`madenat_test`); sin commit/push/despliegue. **Brecha H-SEC-5 pendiente** (la bitácora aún puede
  alterarse). Expediente `AUDITORIA_INTEGRAL_20261012/fase3/`.

## [18.0.6.7.0] - 2026-10-12
### Fixed
- **Diagnóstico `stock_quant_lot_id_fkey` (etiqueta SV con existencias).** El intento de **eliminar**
  desde el visor estándar de lotes una etiqueta SV con existencia física (+40.315 m³ en `WH/Stock`) se
  bloqueaba con el **mensaje técnico** de PostgreSQL (`stock_quant_lot_id_fkey`, ON DELETE RESTRICT).
  **La causa no era un defecto** (el sistema protegía correctamente el historial), pero el mensaje era
  ininteligible para Operaciones.
  - **Opción 2 (guarda proactiva):** `stock.lot._sv_guard_unlink()` ahora bloquea **antes** de la BD la
    **etiqueta SV de volumen con filas en `stock.quant`** (mismo criterio exacto que la FK: existencia de
    fila, aunque la cantidad sea 0) con un mensaje de negocio; el caso legítimo (sin existencias ni
    historial) sigue permitido. Se conserva intacto el bypass test-only por marcador.
  - **Opción 1 (traducción):** `stock.lot.unlink()` traduce la `ForeignKeyViolation` a un mensaje de
    negocio (con `savepoint` para dejar la transacción utilizable). **No** altera el invariante: el lote
    sigue sin poder eliminarse.
### Added
- **Pruebas:** `tests/test_sv_lot_unlink_guard.py` (4 pruebas: guarda con/sin existencias, bypass test-only
  intacto, y traducción del error de FK).

## [18.0.6.6.0] - 2026-10-10
### Added
- **Auditoría (CANON/19 §19.11) — valores ADITIVOS del `Selection` `madenat.audit.log.action_type`:**
  `processor_return_link` («Conciliación Envío–Retorno (procesador)») y
  `processor_return_link_reverse` («Reversa de Conciliación Envío–Retorno»). No reemplazan valores
  existentes; los emite `madenat_lumber_logistics` en la relación de conciliación envío–retorno.

## [18.0.6.5.0] - 2026-10-02
### Added
- **H1: Reversión física ASISTIDA de producción histórica (sin llave fuerte G2).**
  - Nuevo wizard `madenat.guia.processing.historical.reverse.wizard` (+ líneas transitorias
    `madenat.guia.processing.historical.reverse.candidate`) que se abre desde el botón
    secundario **«🧭 Reversión histórica asistida»** del formulario de Guía. Es aditivo: **no**
    modifica ni sustituye G1 (`action_reopen_to_draft` / `_reopen_to_draft_confirmed`),
    G2/G3 (`guia_processing_id` / `_attributed_production_pickings` /
    `_reverse_production_picking`) ni BT-04 (`_reverse_consumption_picking`).
  - Alcance EXCLUSIVO: guías de producción **no** `granel`, **sin** consumo BT-04
    (`consumption_picking_id`) y **sin** producción atribuida por la llave fuerte G2
    (`_h1_is_historical_production()`; campo computed `can_historical_reverse`).
  - **Sin atribución automática**: `origin`, `lot_id`, producto, proveedor, texto y fecha son
    **señales** de propuesta. Clasificación A (origen exacto + cobertura total de lotes +
    incoming/done + sin retorno ⇒ preseleccionado), B (una señal media / evidencia parcial ⇒
    visible, no preseleccionado, selección explícita) y C (excluido: prefijo histórico, retorno
    previo, granel/SV, sin evidencia, compañía ajena, no-`done`, no-`incoming`, FK G2, recepción).
  - **Solo retorno TOTAL por picking** seleccionado (`_h1_reverse_picking_total`): picking de salida
    inverso nativo (picking/move/move.line) preservando producto, UoM, lote, ubicaciones, owner,
    paquete, compañía y `origin_returned_move_id`/`return_id`. **Idempotente** (retorno previo ⇒
    no se propone ni se permite; reintento reutiliza). Nunca escribe/borra `stock.quant`, nunca
    borra/desvincula lotes, pickings, moves, move lines ni `lot_ids`.
  - El operador no queda bloqueado: puede seleccionar candidatos y confirmar, o **no seleccionar
    ninguno** (sin efecto físico). Motivo obligatorio **solo** con efecto físico. Warnings
    (contenedor, quant externo, costos, albarán externo, granel/BT-04/FK) nunca bloquean.
  - Auditoría `madenat.audit.log` `action_type='deviation'` (snapshot JSON + SHA-256, usuario,
    motivo, selección, retornos, omitidos, warnings, lotes) + chatter de la guía.
  - ACL para ambos modelos transitorios (`base.group_user`). Cobertura nueva:
    `TestGuiaHistoricalReverse` (T-H1-01..11).
  - Validación: suite `madenat_lumber_core`, 304 tests, 0 fallos, 0 errores (292 baseline + 12 H1);
    regression H1 en `--test-tags h1`: 12 tests, 0 fallos, 0 errores.

### Fixed
- Desacoplada la extensión de vistas core de `contacts.menu_contacts`;
  el menú Contacts no es una dependencia funcional de MADENAT core y
  ya no bloquea instalaciones limpias sin la aplicación Contacts.

## [18.0.5.5.0] - 2026-09-20
### Added
- **AD-66: Consumo parcial de lote/pool para salida a proceso.**
  - Nuevo modelo `madenat.guia.processing.source.lot.line` (`guia_processing_id` M2O cascade, `lot_id` M2O `stock.lot` ondelete restrict, `qty_to_consume` Float `digits=(16,3)`), con constraint de rango `0 < qty_to_consume <= lot.volumen_m3`.
  - Nuevo campo `source_lot_line_ids` (One2many) en `madenat.guia.processing`, coexistiendo con `source_lot_ids` (M2M legacy/fallback) sin reemplazarlo.
  - `_get_or_create_consumption_picking()`: rama condicional — si `source_lot_line_ids` tiene datos usa `qty_to_consume` por línea; si está vacío, fallback a `qty = lot.volumen_m3` (cero regresión). Auditoría y chatter reportan la cantidad real por lote.
  - `_reverse_consumption_picking()` y `action_force_cancel()` sin cambios (ya leen `move.quantity or move.product_uom_qty`).
  - ACL para el nuevo modelo (`base.group_user`, patrón de `madenat.guia.processing.line`).
  - Cobertura nueva: `TestGuiaProcessingConsumptionPartialAD66` (consumo parcial, bloqueo por exceso, bloqueo por cero/negativo, fallback legacy, reversión parcial).

## [18.0.5.11.0] - 2026-08-16
### Added
- **BT-04: Salida controlada a proceso para guías service.**
  - Guías `tipo_recepcion='service'` generan **exactamente una** salida de stock hacia `Virtual Locations/Production` (picking `outgoing`), reutilizando el patrón de consumo de `madenat_toll_processing`. No se usa `stock.scrap`.
  - Nuevos campos en `madenat.guia.processing`: `source_lot_ids` (M2M, trazabilidad informativa del material crudo) y `consumption_picking_id` (Many2one `stock.picking`, idempotencia).
  - `_get_or_create_consumption_picking()`: guard de contrato (service-only), bloqueo si no hay lote crudo válido, creación de picking/move/move.line por lote y validación automática.
  - `_reverse_consumption_picking()`: retorno entrante inverso que repone el quant del lote crudo copiando las `move_line` originales; el picking original permanece en `done`.
  - Hook `action_validate()` (solo service) antes del ingreso del lote procesado; reversión integrada en `action_force_cancel()` y `action_reopen_to_draft()`.
  - `madenat.audit.log` gana el `action_type='consumption'`.
  - `compra` queda intacto (sin salida).
  - Cobertura nueva: `TestGuiaProcessingConsumptionBT04` (salida única, revalidación sin duplicar, compra sin salida, reversión sin borrar historia, bloqueo sin lote).
  - Validación: `py_compile` OK; selector `guia_processing` 46 tests, 0 fallos, 0 errores; suite `madenat_lumber_core` 79 tests, 0 fallos, 0 errores.
  - Riesgo residual: las mermas reales del proceso (yield) no se modelan como scrap; no se retro-aplica la salida a las 2 guías `service` históricas.

## [18.0.5.10.0] - 2026-08-16
### Fixed
- **BT-01: Notarización y bitácora inmutable para guía processing.**
  - `Gate3PreCommit.generate_processing_signature()` (nuevo) firma un snapshot determinista específico de guía con SHA-256. No modifica `generate_signature()` de recepción.
  - `action_validate()` genera la firma ANTES del primer write a `stock.lot` y persiste al final, solo si el ciclo fue exitoso (misma transacción → sin eventos huérfanos).
  - `madenat.audit.log` gana `guia_processing_id` (Many2one, `ondelete='set null'`), `audit_snapshot`, `audit_hash` y el `action_type='validation_signature'`. La bitácora es la fuente de verdad inmutable.
  - Revalidación genera un evento nuevo; cancelar/reabrir no borra ni altera eventos previos.
  - Recepción y Gate 3 existente conservan exactamente su comportamiento. BT-02 no se reabrió.
  - Cobertura nueva: `TestGuiaProcessingValidationSignature` (firma, persistencia del evento, bloqueo sin evento, supervivencia ante cancelación).
  - Validación: suite `madenat_lumber_core`, 50 tests, 0 fallos, 0 errores.

- **BT-03: Bitácora operativa de lotes en guía processing.**
  - `_create_or_get_lot()` emite `lot_creation` (lote nuevo) o `lot_update` (reutilización idempotente de lote sin `reception_id`), enlazados a `guia_processing_id` en `madenat.audit.log`.
  - `_validar_y_enriquecer_lineas()` emite `omission` para líneas del Excel descartadas antes de crear lote (sin código interno / cantidad <= 0 / dimensiones no numéricas o <= 0), reutilizando la semántica de recepción.
  - Un único evento por outcome confirmado; los `write()` posteriores de `do_full_processing` no duplican `lot_update`.
  - No se modela todavía la baja formal de lotes/etiquetas (fuera de alcance).
  - Cobertura nueva: `TestGuiaProcessingOperationalAudit` (creación, reutilización, omisión, coexistencia con `validation_signature`).
  - Validación: suite `madenat_lumber_core`, 54 tests, 0 fallos, 0 errores.

- **BT-02: Protección de lotes de recepción desde guía processing.**
  - `_create_or_get_lot()` en `madenat_guia_processing.py` ahora excluye explícitamente lotes con `reception_id` en la búsqueda inicial y en el fallback posterior a `IntegrityError`: `('reception_id', '=', False)`.
  - Un lote originado en recepción no puede reutilizarse ni sobrescribirse desde guía processing aunque coincidan nombre, producto y compañía.
  - Se preserva la idempotencia de lotes sin `reception_id` del flujo de guía processing.
  - Cobertura nueva: `TestCreateOrGetLotReceptionProtection` (protección de lote de recepción + reutilización legítima de lote sin recepción).
  - Validación: suite `madenat_lumber_core`, 46 tests, 0 fallos, 0 errores.
  - Sin cambios a Gate 3, auditoría, S2S/Blank, constraints, XML, seeds, Docker ni datos persistentes.

## [18.0.5.9.0] - 2026-07-08
### Refactored
- **AD-43: Unificada `_get_fraction_text` duplicada** en `utils_uom.py` como `decimal_inch_to_fraction_simple(value, denominator=8, tolerance=0.05)`. Eliminadas dos implementaciones divergentes en `madenat_guia_processing.py:542` (base-8 con tolerancia 0.05) y `lumber_reception.py:647` (base-16 con gcd). Wrappers de 1 línea en ambos archivos. Comportamiento preservado: base-8 para guías/S2S, base-16 para recepciones/Blanks. Registry cargado en 2.657s, 0 errores.

## [18.0.5.8.0] - 2026-07-08
### Refactored
- **AD-42:** Extraída `_parse_float_value` de `madenat_guia_processing.py` a utilidad compartida `parse_float_value` en `utils_uom.py`. Mismo patrón AD-41: función pura + wrapper delegado. 11 call sites. Heurísticas CLP, mm→m, mm→cm preservadas intactas. Registry cargado en 2.726s, 0 errores.

## [18.0.5.7.0] - 2026-07-08
### Refactored
- Extraída `_parse_fraction` de `madenat_guia_processing.py` a utilidad compartida `parse_fraction_to_decimal_inch` en `utils_uom.py`. Consolidada duplicación con `stock_lot._parse_fraction_to_decimal`. Sin cambios de comportamiento (12 tests unitarios). AD-41.

## [18.0.5.6.0] - 2026-07-06
### Changed
- **Consolidación de `reception_service.cleanup_orphan_moves()` hacia savepoint**
  - Estrategia de unlink homogeneizada: `savepoint + with_context(force_delete=True).unlink()` en ambos métodos sobrevivientes.
  - Validado con Tests A y B (Fase 3a): 0 failed, 0 error(s).
  - Asimetría transaccional documentada en Fase 2 eliminada.
  - **Commit:** `e6a1fc1`
  - **Ver AD-39 (cierre funcional) y sección W de `AUDITORIA_ASIMETRIA_DOCUMENTAL_20260706.md`.**

## [18.0.5.5.0] - 2026-07-06
### Removed
- **Eliminado `_cleanup_orphan_moves()` de `lumber_reception.py` (código muerto)**
  - **Evidencia:** 0 callers en producción. Confirmado por grep exhaustivo en todo custom_addons.
  - **Motivo:** Método duplicado (90% idéntico a `cleanup_orphan_moves()` en `reception_service.py:167` y `_cleanup_orphan_moves_guia()` en `madenat_guia_processing.py:4303`). Los 3 ya contienen el FIX 2026-07-01 (protección quantity > 0).
  - **Archivado en:** `_archive/_cleanup_orphan_moves.py` con documentación de procedencia y checkpoint de rollback.
  - **Ver AD-38 en `04_DECISION_LOG.md`.**
  - **Commit:** `9677f53` (checkpoint rollback: `56ef417`).
  - **Validación:** py_compile OK, módulo actualizado en Docker sin errores, 0 referencias rotas.

## [18.0.5.4.0] - 2026-07-01
### Fixed
- **UserError al eliminar stock.moves con cantidad recolectada (quantity > 0)**
  - **Causa raíz:** `action_reopen_to_draft()` FASE 3 desvincula pickings `done` internos sin cancelarlos, generando moves huérfanos.
  - **Solución:** Filtrar moves con `move_line_ids.quantity > 0` → marcar como `"HUERFANO-PROTEGIDO-"`; solo eliminar `cleanable_moves` (quantity == 0). Fix en 3 archivos: `madenat_guia_processing.py`, `lumber_reception.py`, `reception_service.py`.
  - **Deuda técnica registrada:** La fuente real es que FASE 3 no cancela pickings `done` internos. Requiere revisión futura.

## [18.0.5.1.0] - 2026-06-11
### Fixed
- **thickness_visual 6/4**: max_thickness 42→46mm, 7/4 min_thickness 42→46mm
- 45mm S2S ahora clasifica correctamente como `6/4` (nominal canónico 1.5")
- Script de migración automática incluido: aplica en upgrade sin intervención manual


### Hotfix
- **[HOTFIX UX] — Pestaña Comercial f5085: Esp. Comercial (thickness_visual) como columna principal, nominal exacto como columna opcional (2026-06-10)**

  **Síntoma:**
  La pestaña "COMERCIAL (INVENTARIO)" mostraba `thickness_nominal_frac` (fracción exacta, ej: "1 1/2") para el perfil f5085, cuando el operador espera ver la representación comercial estándar de cuartos (ej: "6/4") que ya se usa en las pestañas Físico y Exportación.

  **Causa raíz:**
  El método `_compute_visual_defaults` (lumber_reception.py L499-538) calcula dos valores distintos para f5085:
  - `thickness_visual` → cuartos comerciales (4/4, 5/4, 6/4, 8/4) vía `_apply_thickness_visual()`
  - `thickness_nominal_frac` → fracción exacta base 16 (ej: "1 1/2") vía `_get_fraction_text()`
  
  La pestaña Comercial renderizaba solo `thickness_nominal_frac`, mostrando la fracción exacta en lugar del cuarto comercial.

  **Corrección (solo XML, 0 Python):**
  - Archivo: `views/lumber_reception_views.xml`
  - Columna principal (visible): `thickness_visual` con string="Esp. Comercial", `readonly="0"`
  - Columna secundaria (oculta): `thickness_nominal_frac` con string="Nom. Exacto", `optional="hide"`
  - `column_invisible` por perfil conservado en ambas: solo visible en f5085
  - El nominal exacto sigue accesible vía menú de columnas (tres puntos > Nom. Exacto)

  **Impacto:**
  - Cero cambios en Python, cálculos matemáticos, exportación, costeo o auditoría
  - Trazabilidad del nominal exacto preservada (columna opcional accesible)
  - Edición manual preservada (`thickness_visual` tiene `readonly=False` en modelo, `readonly="0"` en vista)
  - Edición masiva preservada (wizard escribe `thickness_nominal` + `thickness_nominal_frac` → ORM recalcula `thickness_visual` vía `@api.depends`)
  - Edición inline preservada (tree tiene `editable="bottom"`)

  **Validación:**
  - Sin cambios en `_compute_visual_defaults`, `_compute_export_values`, `_compute_volume_purchase`, `_compute_line_cost`
  - Sin cambios en f1550, metric (`column_invisible` los oculta)
  - Sin cambios en gate GB-1, nominal_status, wizard de asignación masiva
  - Sin cambios en auditoría (audit_snapshot), exportación Excel, validación documental
  - Sin pérdida de trazabilidad: el nominal exacto queda disponible como columna opcional

- **[HOTFIX v4] — Búsqueda de lote tolera company_id=NULL (2026-06-04)**

  **Evidencia de BD:**
  ```sql
  SELECT id, name, product_id, company_id FROM stock_lot WHERE id = 1605;
  -- Resultado: company_id IS NULL, guia_processing_id IS NULL
  ```
  El lote `D7731 PCLAT04201253250 19846` existe en BD desde 2026-04-03 con `company_id=NULL`. Tanto la búsqueda primaria como el fallback usaban `('company_id', '=', 1)`, donde `NULL = 1` es falso en SQL — el lote nunca era encontrado. Esto forzaba la rama `create()` que disparaba la colisión UNIQUE, y el fallback repetía la misma búsqueda fallida.

  **Corrección (v4):**
  - Ambas búsquedas ahora usan `('company_id', 'in', [self.env.company.id, False])` con `order='company_id DESC'`. El `write(vals)` subsiguiente establece `company_id` correctamente, reparando lotes huérfanos.

  **Impacto:**
  - Sin cambios en `action_reopen_to_draft()`, `do_full_processing()`, `action_validate()`.
  - Sin `unlink()` de lotes — trazabilidad preservada.
  - Corrige datos legados (lotes huérfanos con company_id=NULL).

  **Validación:**
  - `py_compile` OK.
  - Pendiente: prueba funcional del ciclo completo.

- **[HOTFIX v3] — Savepoint en create() para limpiar transacción tras IntegrityError (2026-06-04)**

  **Hallazgo forense (logs 00:50–00:53):**
  - v2 sí entra al fallback: `⚠️ Colisión UNIQUE... reutilizando lote existente` aparece a las 00:53:10,980.
  - Pero 17 ms después (00:53:10,997) el error de unicidad **sigue propagándose** al usuario.
  - **Causa real:** psycopg2 requiere que una transacción que sufre `IntegrityError` haga rollback completo antes de cualquier otra operación. Aunque `except` capturaba la excepción, el cursor seguía tainted, y el `lot.search()` + `lot.write(vals)` del fallback fallaban silenciosamente, re-lanzando la misma `IntegrityError` al confirmar la transacción.

  **Corrección (v3):**
  - `_create_or_get_lot()` línea 2640: el `create()` ahora se ejecuta dentro de `with self.env.cr.savepoint():`. El savepoint aísla la colisión UNIQUE: si falla, solo se descarta ese sub-bloque y el cursor queda limpio para el fallback de re-búsqueda y `write()`.

  **Validación:**
  - `py_compile` OK.
  - Reinicio de Odoo OK.
  - Pendiente: prueba funcional del ciclo completo (procesar → reenviar a borrador → revalidar).

- **[HOTFIX v2] — _create_or_get_lot() ahora captura ValidationError (2026-06-04)**

  **Hallazgo de logs (post commit 09c870d):**
  - Las trazas muestran `✨ Creando lote D7731...` en cada reproceso, pero **nunca** aparece el log `⚠️ Colisión UNIQUE...` del fallback.
  - El error visible al usuario sigue siendo: `"Error de validación: La combinación de número de serie o lote y producto debe ser única..."`
  - **Causa real del bypass:** Odoo captura el `IntegrityError` de psycopg2 en la capa ORM (`_sql_constraints`) y lo re-lanza como `ValidationError`. Por lo tanto, nuestro `except IntegrityError` **nunca se ejecutaba** — el `create()` lanzaba `ValidationError` directamente al usuario, que es lo mismo que se veía antes del hotfix.

  **Corrección (v2):**
  - `_create_or_get_lot()` línea 2641: `except (IntegrityError, ValidationError):` — ahora captura ambas excepciones. El fallback de re-búsqueda y reutilización del lote existente se ejecutará correctamente ante colisiones UNIQUE de `_sql_constraints`.

  **Validación:**
  - `py_compile` OK.
  - Reinicio de Odoo OK.
  - Pendiente: prueba funcional del ciclo completo (procesar → reenviar a borrador → revalidar).

- **[HOTFIX v1] — _create_or_get_lot() tolera colisión de unicidad al reprocesar guía (2026-06-04)**

  **Causa raíz confirmada:**
  - `action_reopen_to_draft()` solo desvincula lotes de la guía (`guia_processing_id = False`) pero el `stock.lot` persiste en BD con su `name`, `product_id` y `company_id`.
  - Al reprocesar, `_create_or_get_lot()` hace `search(name, product_id, company_id)` — si por cualquier motivo no encuentra el lote existente, ejecuta `create()` y PostgreSQL lanza `IntegrityError` por la constraint `UNIQUE(name, product_id, company_id)` nativa de `stock.lot`.
  - Sin cambios en la lógica de `action_reopen_to_draft()` ni en `do_full_processing()` ni en `action_validate()`.

  **Cambio aplicado (v1):**
  - `_create_or_get_lot()` (línea ~2639): el `self.env['stock.lot'].create(vals)` ahora está envuelto en `try/except IntegrityError`. Si ocurre la colisión, el método invalida caché, re-busca el lote existente y lo reutiliza con `write(vals)`. Solo re-lanza la excepción si realmente no aparece.

  **Impacto:**
  - Sin cambios en `action_reopen_to_draft()`, `do_full_processing()`, `action_validate()`, ni `action_force_cancel()`.
  - Sin `unlink()` de lotes — los lotes permanecen en BD para trazabilidad.
  - Sin cambios en lógica de stock, pickings ni moves.
  - El método es ahora idempotente ante reproceso desde borrador.

  **Validación:**
  - `py_compile` OK.
  - Reinicio de Odoo OK.
  - Pendiente: prueba funcional del ciclo completo (procesar → reenviar a borrador → revalidar).

- **[HOTFIX] — Duplicados al reenviar guía a borrador (2026-06-04)**

  **Causa raíz:**
  - `_get_or_create_picking_unified()` no excluía pickings en estado `done`, permitiendo reutilizar pickings cerrados como si fueran nuevos.
  - `action_reopen_to_draft()` realizaba cancel y rename en bloque, dejando el `origin` sin modificar si `action_cancel()` fallaba en algún picking.

  **Cambios aplicados:**
  1. `_get_or_create_picking_unified()` línea 1664: search excluye ahora `done` y `cancel` → `('state', 'not in', ['cancel', 'done'])`
  2. `action_reopen_to_draft()` línea 3170: iteración individual con try/except garantiza que el rename se ejecute aunque cancel falle.

  **Impacto:**
  - Sin cambios en lógica de lotes.
  - Sin cambios en flujo de stock confirmado.
  - Sin cambios en validación de duplicados reales.

  **Validación:**
  - py_compile OK.
  - Sin tocar lotes, `action_force_cancel()`, `_cleanup_orphan_moves_guia()`, `do_full_processing()` ni `_create_or_get_lot()`.

- Corregido error `unsupported operand type(s) for +: 'float' and 'decimal.Decimal'` en procesamiento Excel (2026-06-04). Causa raíz: `get_s2s_adjustment()` retorna `Decimal` pero se usaba en aritmética con `float` en dos sitios de `madenat_guia_processing.py` sin conversión. Solución mínima: `float(ajuste_s2s)` en `_validar_y_enriquecer_lineas:2290` y `float(recargo)` en `_compute_vol_shipment_m3:512`. Sin cambios en lógica de lotes, líneas de detalle, paquetes, volúmenes ni conteos. Sintaxis OK.

- Corregido `UnboundLocalError` por sombreado de constante importada `M_TO_FT` en guía processing (2026-06-04). Causa raíz: `M_TO_FT = float(M_TO_FT)` en dos métodos (`_compute_vol_mbf:413`, `_compute_imperial_values:263`) reasignaba localmente el nombre de la constante importada desde `utils_uom.py`, causando que Python la interpretara como variable local en todo el scope. Solución mínima: renombrar variable local a `m_to_ft` en ambas funciones. Sin cambios en lógica de negocio, lotes, líneas ni paquetes. Sintaxis y reinicio de Odoo OK.

### Refactored
- TD-009: Centralizar `LUMBER_DIMENSION_MAP` en `utils_uom.py` (2026-06-04). Dict movido sin modificaciones desde `madenat_guia_processing.py:22-61` a `utils_uom.py:733`. Import extendido en `guia_processing.py:63-75`. Preparatorio para TD-010 (migración a modelos ORM configurables). 43 líneas eliminadas de `guia_processing.py`. Comportamiento funcional idéntico.

### Research
- TD-006: Investigación de parametrización de reglas comerciales (`+1/8"`, `1550.003096`, `5085.312`) — conclusión: NO parametrizable. Las 6 fuentes de evidencia (código, git log, docs, modelo de configuración) confirman que las reglas son fijas para todo MADENAT. Sin evidencia de variación por cliente/perfil/subproducto. Documentado en WIKI y CANON con condiciones de reapertura.

### Documentation
- TD-005.1: Comentario explicativo expandido en `INCH_SQ_METERS_TO_M3 = 1550.003096` documentando origen dimensional exacto (NIST), fórmula de derivación, y uso en cubicación comercial de embarque. Nota complementaria en WIKI TD-005.

### Fixed
- TD-004: Centralización de constante física universal `25.4` → `MM_PER_INCH` en `lumber_reception_mass_update.py:114`
- TD-005: Clasificación y parametrización de reglas de negocio comercial. Documentado inventario completo de constantes: `M3_DIVISOR` (1000000), `FACTOR_EMBARQUE` (1550.003), `FACTOR_BLANK` (5085.312), `MBF_DIVISOR` (12000), `S2S_WIDTH_ADJUSTMENT_INCH` (0.125). Todas ya centralizadas en `utils_uom.py`. Corrección menor: `lumber_shipment_line.py:131` usaba `1_000_000.0` literal → `float(M3_DIVISOR)`.

## [1.5.0] - 2025-12-13
### Added
- **Trazabilidad:** Nuevo campo `source_shipment_cost_line_id` en `stock.lot.cost.line` para vincular costos con su origen en embarques.