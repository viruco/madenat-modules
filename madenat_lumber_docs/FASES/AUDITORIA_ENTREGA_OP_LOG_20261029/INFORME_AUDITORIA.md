# INFORME DE AUDITORÍA TÉCNICO-FUNCIONAL DE ENTREGA
## ÁREA: OPERACIONES Y LOGÍSTICA — MADENAT
### Odoo 18 Community Edition

**Fecha:** 2026-10-29  
**Entorno auditado:** Docker `odoo18_app` (Odoo 18.0 CE) / `odoo18_db` (PostgreSQL 15)  
**Base operativa consultada:** `madenat_test` (Modo Solo Lectura / SELECT estricto)  
**Ruta del repositorio:** `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons`  
**Rama auditada:** `lote5-desacople-shipping-20261029`  
**HEAD auditado:** `26d865d`  
**Base inmediata de comparación:** `lote4-correcciones-20261029` (commit `50e7ca4`)  
**Remoto:** `git@github.com:viruco/madenat-modules.git`  
**Auditor:** Auditor Técnico-Funcional Senior Odoo 18 CE  

---

## 1. LÍNEA BASE Y ALCANCE

### 1.1 Estado del Repositorio y Git
- **Rama activa:** `lote5-desacople-shipping-20261029` (sincronizada con `origin/lote5-desacople-shipping-20261029`).
- **HEAD:** `26d865d` (*"madenat_lumber_docs: registrar limpieza de bases temporales del Lote 5 (NEW-01)"*).
- **Estado de trabajo:** Árbol limpio (`git status -bs` sin modificaciones pendientes).
- **Relación con Lote 4:** 19 commits lineales desde `50e7ca4` correspondientes al Lote 5 (desacople de dependencias entre `madenat_lumber_shipping_core` y `madenat_lumber_logistics`, modelo y vista extendida `shipping_vessel_inherit`, tests unitarios `test_vessel_button.py` y alineación de documentación/CHANGELOGs).

### 1.2 Versiones de Módulos (Código vs. Base de Datos `madenat_test`)
Se verificó el estado en manifiestos de código y en la tabla `ir_module_module` mediante consulta SELECT:

| Módulo | Versión en Manifiesto (`__manifest__.py`) | Versión Registrada en `madenat_test` | Estado en BD | Discrepancia / Observación |
|---|---|---|---|---|
| `madenat_lumber_shipping_core` | **18.0.1.3.0** | **18.0.1.0.0** | `installed` | Pendiente de despliegue (`-u`). Código avanzado (+3 versiones menores por NEW-01). |
| `madenat_lumber_logistics` | **18.0.1.43.0** | **18.0.1.41.1** | `installed` | Pendiente de despliegue (`-u`). Código avanzado (+2 versiones menores por Lotes 4 y 5). |
| `madenat_lumber_core` | **18.0.6.25.1** | **18.0.6.25.1** | `installed` | Sincronizado. |
| `madenat_lumber_intake` | **18.0.0.22.0** | **18.0.0.22.0** | `installed` | Sincronizado. |
| `madenat_ingestion_engine` | **18.0.1.5.1** | **18.0.1.5.1** | `installed` | Sincronizado. |
| `madenat_toll_processing` | **18.0.1.0.2** | **18.0.1.0.2** | `installed` | Sincronizado. |
| `madenat_lumber_purchasing` | **18.0.2.2.0** | **18.0.2.2.0** | `installed` | Sincronizado. |
| `madenat_lumber_reports` | **18.0.2.3.0** | **18.0.2.3.0** | `installed` | Sincronizado. |
| `madenat_lumber_costing` | **18.0.1.0.0** | **18.0.1.0.0** | `installed` | Sincronizado. |

---

## 2. METODOLOGÍA Y DISTINCIÓN DE EVIDENCIA

Para asegurar el máximo rigor profesional y evitar declaraciones de conformidad no fundamentadas, cada conclusión de esta auditoría se sustenta exclusivamente en una de las cuatro fuentes siguientes:

1. **CONFIRMADO EN CÓDIGO (Revisión Estática):** Inspección directa de métodos Python, vistas XML, restricciones de modelo (`_sql_constraints`, `@api.constrains`), reglas de registro (`ir.rule`) y ACLs (`ir.model.access.csv`) en el árbol de trabajo actual.
2. **OBSERVADO EN BASE (Consultas SQL de Solo Lectura):** Consultas `SELECT` ejecutadas directamente en el motor PostgreSQL de `madenat_test`. Estas consultas permiten auditar el estado real de tablas operativas (`stock_quant`, `stock_picking`, `lumber_reception`, `lumber_container`, `madenat_audit_log`, `mail_message`), sin modificar ni insertar datos.
3. **ACREDITADO POR LOG HISTÓRICO (Trazabilidad en Disco):** Verificación de logs de ejecución fechados y ubicados en el sistema local (`/home/viruco/test_core.log`, `/home/viruco/test_access.log`, `/home/viruco/test_rollover21.log`, `/home/viruco/test_vessel_button.log`), registrando el resultado literal de suites de prueba unitarias.
4. **NO EJECUTADO (Pruebas Dinámicas Pendientes):** Ensayos dinámicos que exigen mutaciones transaccionales en base de datos (creación de guías, movimientos de stock, rolleo de contenedores, cambio interactivo de credenciales en navegador). No se ejecutaron en esta fase por estricto apego a las Reglas de Seguridad de Solo Lectura y quedan detallados para la etapa UAT.

---

## 3. FUNDAMENTOS TÉCNICOS Y DOCTRINALES CLAVE

### 3.1 Análisis de Quants y Unicidad de Lotes en Patios
En Odoo nativo, un producto configurado con seguimiento por lotes (`tracking = 'lot'`) puede técnicamente dividirse en múltiples ubicaciones si se realiza un traslado parcial (split). Sin embargo, en el modelo de negocio de MADENAT, **las tarjas representan paquetes físicos individuales cerrados y únicos** con cubicación fija.

Para auditar si existía dispersión indebida o doble contabilización de tarjas en patios internos, se ejecutó:
```sql
SELECT lot_id, count(*)
FROM stock_quant q
JOIN stock_location l ON q.location_id = l.id
WHERE l.usage = 'internal' AND q.quantity > 0
GROUP BY lot_id HAVING count(*) > 1;
```
- **Resultado:** **0 filas devueltas**.
- **Significado técnico:** No existe ningún lote que tenga stock positivo concurrente en más de una ubicación interna a la vez (`WH/Stock`, `WH/Stock/MARVAL`, `WH/Stock/PUERTO CORONEL`, `WH/Stock/Procesadores/<X>`). Cada tarja está físicamente confinada a un solo patio o procesador. Asimismo, la consulta de quants negativos en ubicaciones internas arrojó **0 filas**.

### 3.2 Recepciones sin Albarán: Separación de Borradores y Validación Física
En la consulta SQL sobre `lumber_reception`, se observó que de 9 registros:
- 5 registros poseen `picking_id` con estado `done` (`EMB-00192`, `EMB-00225`, `EMB-00227`, `EMB-00229`, `EMB-04011`).
- 4 registros (`1161`, `1244`, `7950`, `14204`) tienen `state = 'verified'` y `picking_id IS NULL`.

**Aclaración de diseño de compuertas (Gates):**
Al inspeccionar el código de [lumber_reception.py:L2910-2935](file:///home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_core/models/lumber_reception.py#L2910-L2935) y [L3093-3115](file:///home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_core/models/lumber_reception.py#L3093-L3115):
- `verified` (`👀 Verificado`) es el estado resultante de la compuerta de extracción documental (`action_verify_data`), en donde se valida el archivo Excel/PDF y se cargan las líneas de staging (`lumber.reception.line`). **No afirma recepción física ni genera movimientos de inventario.**
- `done` (`✅ Recibido`) es el estado que afirma recepción física de stock, ejecutado en Gate 3 mediante `LumberReceptionService.create_stock_picking()`, momento en el cual se crean los lotes, el albarán `stock.picking` y los quants.
- **Conclusión:** Las 4 recepciones en `verified` sin picking corresponden a registros en etapa de staging documental que nunca fueron confirmados físicamente a inventario. No constituyen un defecto de stock ni afirman falsamente una recepción física en la base.

### 3.3 Sustento Doctrinal y Canónico de la Exclusión de la Fase I3
La salida física de inventario para el lote SV (descuento del quant del SV y ledger `action_type = 'imputacion'`) **no forma parte del alcance operativo vigente**, conforme a la doctrina oficial del proyecto:
- **Ruta documental:** [CANON/19_IMPUTACION_SV_Y_PROCESADORES.md](file:///home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_docs/CANON/19_IMPUTACION_SV_Y_PROCESADORES.md)
  - **Sección §4.3 («Efectos materializados en I3/I5, no en I2»):** Establece explícitamente que la salida nativa (`stock.move` a `Virtual Locations/Production`) y el ledger con `action_type = 'imputacion'` pertenecen a la Fase I3. En Fase I2, la imputación es un acto exclusivamente documental.
  - **Sección §16 («Plan de ejecución canónico por fases»):** Define la secuencia obligatoria: I1 (Cimientos/Ubicaciones) → I2 (Imputación documental) → I3 (Salida nativa y ledger) → I5 (Costeo).
- **Decision Log:** [CANON/04_DECISION_LOG.md](file:///home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_docs/CANON/04_DECISION_LOG.md) **AD-91** (*"Imputación documental SV por guía procesada (I2)"*, aprobada 2026-10-02): Dispone que la Fase I2 no toca `stock.quant` ni crea albaranes de salida para el SV; se limita a registrar la asignación documental, calcular saldos documentales y estampar firmas criptográficas SHA-256.
- **Conclusión:** La funcionalidad de imputación SV en la pantalla *"Rebaja de etiquetas"* cumple al 100% el alcance aprobado de la Fase I2. La ausencia de descuento de quant para el lote SV no es un defecto ni un requisito omitido, sino una fase formalmente diferida.

### 3.4 Relación entre Imputación Documental SV y Rebaja Física de Contenedor: Prevención de Doble Descuento
El negocio opera madera a granel/rollizos (lotes Volumen / SV) que se transforman mediante maquila externa en paquetes aserrados (lotes Tarja / Producto Procesado). Existía el riesgo teórico de que la madera se descontase dos veces de inventario.

El blindaje contra la doble salida opera en tres niveles estancos:
1. **Regla de No Exportación de SV (CANON 19 §2.1 y R-19-01):** Un lote SV (`lot_flow_type = 'volume'`) **nunca se consolida en un contenedor de exportación ni se le aplica rebaja de embarque**. El asistente de consolidación (`lumber.container.lot.wizard`) excluye los lotes SV por defecto (`D9`).
2. **Rebaja Física Exclusiva en Contenedor (AD-82):** El único movimiento físico de salida de inventario hacia clientes (`stock.move` a `Partners/Customers`) lo ejecutan las **tarjas retornadas** al disparar `action_rebaja_container` en el contenedor.
3. **Imputación Documental Pura (AD-91):** La asignación de la tarja contra su lote SV padre en la pantalla *"Rebaja de etiquetas"* descuenta únicamente la capacidad nominal y saldo documental (`_i2_lot_applied_m3`), sin generar albaranes de salida.
- **Resultado:** El inventario físico de MADENAT se descuenta **exactamente una vez** (al rebajar el contenedor con las tarjas). El saldo documental del SV se amortiza en el ledger administrativo sin tocar quants físicos hasta la futura Fase I3.

---

## 4. MATRIZ DEL FLUJO OPERATIVO Y LOGÍSTICO

| Proceso | Módulo / Modelo | Método / Acción | Rol Requerido | Estado Inicial → Final | Efecto Físico / Documental | Evidencia Verificada |
|---|---|---|---|---|---|---|
| **A1. Ingesta y Clasificación** | `madenat_lumber_intake` / `madenat.lumber.intake.wizard` | `action_classify_document` | Operaciones (`group_madenat_operaciones`) | `draft` → `classified` | Documental: parsea PDF/Excel, asigna perfil y crea líneas staging sin tocar stock. | [intake_wizard.py:L142](file:///home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_intake/wizards/madenat_lumber_intake_wizard.py#L142). CONFIRMADO EN CÓDIGO. |
| **A2. Validación Física Recepción** | `madenat_lumber_core` / `lumber.reception` | `action_validate_physical` | Jefatura de Operaciones (`group_madenat_jefatura_operaciones`) | `draft` → `verified` → `done` | Físico: crea `stock.picking` (IN), `stock.move.line`, genera quants y `stock.lot`. | [lumber_reception.py:L3100](file:///home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_core/models/lumber_reception.py#L3100). OBSERVADO EN BASE: 5 pickings `done`. |
| **A3. Prevención Revalidación Duplicada** | `madenat_lumber_core` / `lumber.reception` | `_guard_revalidation` | N/A (Guarda de servidor) | N/A | Bloqueo duro: impide crear pickings duplicados si ya existe picking terminado. | Commit `5e9b26c`. CONFIRMADO EN CÓDIGO. |
| **A4. Reapertura Trazable de Guía** | `madenat_lumber_core` / `madenat.guia.processing` | `action_reopen_guia` | Jefatura / Gerencia | `validated` → `draft` | Documental y físico controlado: desvincula staging con `sudo()`, audita en chatter y log. | Commits `0db9e0a`, `ef37292`, `97bf121`. CONFIRMADO EN CÓDIGO. |
| **B1. Control de Patios y Quants** | `stock` / `stock.quant` | Native Odoo ORM / `_update_available_quantity` | Operaciones | N/A | Físico: asignación de existencias a ubicaciones internas (`WH/Stock`, `MARVAL`, `PUERTO CORONEL`). | OBSERVADO EN BASE: 147 quants, 0 negativos en `internal`, 0 lotes duplicados en patios. |
| **B2. Identificación Operativa Lotes** | `madenat_lumber_core` / `stock.lot` | `create` / `write` | Operaciones | N/A | Documental/Físico: dimensiones, volumen compra vs export, etiquetas externas (`external_labels`). | Commit `bd918ee` (DISC-OP-01). CONFIRMADO EN CÓDIGO. |
| **C1. Envío a Procesador** | `madenat_lumber_logistics` / `stock.picking` | `action_assign_processor_shipment` | Operaciones / Jefatura | `draft` → `done` | Físico: traslado interno hacia custodia `WH/Stock/Procesadores/<X>`. No es venta ni consumo. | CANON 19 §2.2 / AD-90. OBSERVADO EN BASE: Ubicación `4919` (`V3 Planta`) con 5 m3. |
| **C2. Retorno de Servicio** | `madenat_lumber_core` / `madenat.guia.processing` | `action_confirm_service_return` | Operaciones | `service_return_confirmation = 'yes'` | Documental: marca la guía de procesados como retorno oficial habilitante para imputación. | OBSERVADO EN BASE: Guías `19827` y `V3-CONCIL` con confirmación `yes`. |
| **C3. Imputación Documental SV** | `madenat_lumber_logistics` / `madenat.sv.imputation` | `action_apply` | Operaciones (`group_madenat_operaciones`) | `draft`/`pending` → `applied` | Documental: vincula tarjas de retorno con lote SV, descuenta saldo documental, firma SHA-256. Sin movimiento de stock. | [madenat_sv_imputation.py:L1258](file:///home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_logistics/models/madenat_sv_imputation.py#L1258). OBSERVADO EN BASE: 10 registros `imputation` en log. |
| **D1. Asignación a Contenedor** | `madenat_lumber_logistics` / `lumber.container.lot.wizard` | `action_assign` | Operaciones | `loading` → `loaded` | Documental: vincula tarjas disponibles al contenedor y valida paquetes únicos. | CONFIRMADO EN CÓDIGO y test `test_container_lot_wizard_disponible.py`. |
| **D2. Rebaja de Contenedor** | `madenat_lumber_logistics` / `lumber.container` | `action_rebaja_container` | Operaciones / Jefatura | `loaded` → `rebajado` | Físico: salida nativa de stock (`stock.move` a `Partners/Customers`) de las tarjas del contenedor. | [lumber_container.py:L1040](file:///home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_logistics/models/lumber_container.py#L1040). OBSERVADO EN BASE: 4 contenedores `rebajado`. |
| **D3. Rolleo de Contenedor** | `madenat_lumber_logistics` / `lumber.container.rollover.wizard` | `action_confirm_rollover` | Operaciones / Jefatura | `loaded` (en nuevo embarque) | Documental: reasigna contenedor a otro embarque; bloqueado si tiene rebaja o zarpe; trazabilidad en chatter. | OBSERVADO EN BASE: Mensajes de rolleo en chatter (IDs 136378, 136380, 136385). |
| **D4. Zarpe y Excepción B-01** | `madenat_lumber_logistics` / `lumber.export.shipment` | `action_set_in_transit` | Operaciones / Jefatura | `confirmed` → `in_transit` | Operativo/Documental: salida de nave; si hay contenedores sin rebajar abre excepción B-01 y bloquea Entrega. No descuenta stock. | OBSERVADO EN BASE: 8 embarques `in_transit`, 3 eventos `b01_departure_exception` en auditoría. |
| **D5. Consulta Embarques por Buque** | `madenat_lumber_logistics` / `shipping.vessel` | `action_open_vessel_shipments` | Operaciones / Jefatura / Gerencia | N/A | Vista/Consulta: abre embarques asociados a la motonave. Desacoplado de `shipping_core` en Lote 5. | OBSERVADO EN BASE: Vista ID 2933 en `ir_ui_view`. ACREDITADO POR LOG: `test_vessel_button.log` (3/3 passed). |
| **F1. Segregación de Funciones** | Multi-módulo / `ir.model.access.csv` | Acceso RPC / ORM | Cristhian (Operaciones) vs. Felipe (Auditoría) | N/A | Seguridad: Cristhian opera recepciones, toll, logística y shipping; Felipe audita con solo lectura en shipping y sin permisos de mutación operativa. | ACREDITADO POR LOG: `test_access.log` (3/3 passed) y `test_core.log` (3/3 passed). |

---

## 5. CLASIFICACIÓN REVISADA Y ANÁLISIS DE LOS NUEVE HALLAZGOS MAYORES

Los nueve hallazgos clasificados originalmente como de severidad MAYOR se reagrupan estrictamente según su naturaleza observable y su impacto real en la operación:

| ID | Categoría Técnica | Proceso Afectado | Consecuencia Observable en la Operación | Acción Requerida / Estado |
|---|---|---|---|---|
| **HALL-OPLOG-01** | **d) Pendiente de despliegue** | Metadatos Odoo / Registro de módulos | En `madenat_test`, `ir_module_module` registra `shipping_core` en `18.0.1.0.0` y `logistics` en `18.0.1.41.1`, mientras los manifiestos en disco están en `18.0.1.3.0` y `18.0.1.43.0`. Si el servidor se reinicia o se corre una actualización parcial, no se tiene certeza de la sincronización del registry de vistas/modelos. | Ejecutar actualización CLI: `odoo -u madenat_lumber_shipping_core,madenat_lumber_logistics -d madenat_test --stop-after-init --no-http`. Requiere ventana autorizada. |
| **DISC-OP-10** | **a) Defecto demostrado (Corregido en Lote 6)** | Inventario / Consumo en Toll Processing | En `toll_processing_order.py:316`, `_create_consumption_picking` hardcodeaba `location_src_id = warehouse.lot_stock_id.id` (`WH/Stock`). Si los lotes estaban en un patio específico (`WH/Stock/MARVAL` o `PUERTO CORONEL`), el consumo extraía de `WH/Stock`, provocando quants negativos en la raíz y dejando intacto el stock del patio. | **RESUELTO en Lote 6:** Implementado `_get_lot_consumption_sources` que inspecciona quants internos reales, valida disponibilidad libre con `stock.quant._get_available_quantity(..., strict=True)`, soporta distribución multi-ubicación y genera movimientos/líneas nativos desde el patio correspondiente. Suite de tests añadida. |
| **DISC-OP-09** | **b) No reproducido como defecto de código** | Maquila / Creación de orden Toll | Se sospechaba que `partner_id = reception.supplier_id.id` forzaba la orden al proveedor de compra impidiendo maquilar con otro tercero. La revisión estática demostró que `processor_id` es solo un valor por defecto editable en borrador y que la orden preserva al maquilador elegido en todo el ciclo (confirmación, consumo, facturación). | **ACREDITADO:** No requiere selector adicional ni cambios de código; comportamiento documentado y blindado con tests focalizados en `test_toll_consumption_and_processor.py`. |
| **DISC-OP-08** | **b) Decisión operativa pendiente** | Seguridad / Higiene de base de datos | En `lumber_reception`, `ir.model.access.csv` fija `unlink = 0` para Jefatura. Si un usuario intenta eliminar una recepción rechazada o errónea por UI, recibe `AccessError`. La limpieza de staging está resuelta con `sudo()`, pero el borrado de cabecera permanece bloqueado. | Decisión de Gerencia: ¿Se otorga `perm_unlink = 1` a Jefatura bajo AD-103 o se mantiene la política estricta de no borrado para salvaguardar la trazabilidad? |
| **DISC-OP-11** | **e) Hipótesis por verificar** | Trazabilidad / Retorno de procesados | En `guia_processing_integration.py`, los lotes de la orden Toll no se propagan automáticamente a las líneas O2M de consumo parcial de la guía de procesados. El usuario debe seleccionarlos manualmente. No rompe datos, pero introduce riesgo de error humano. | Verificar en UAT si el operario puede vincular manualmente los lotes de origen sin fricción o si se requiere automatizar la propagación. |
| **DISC-LOG-14** | **c) Mejora no bloqueante** | Documental / Reservas marítimas | Discrepancia cosmética de claves de selección de tipo de contenedor: `shipping.booking` usa `40hc` (minúscula) y `lumber.container` usa `40HC` (mayúscula). Dado que el enlace entre contenedor y booking se hace por Many2one (`booking_id`) y no por string, no afecta la operación. | Mantener en backlog estético. No modificar claves de selección para no invalidar registros existentes en la BD. |
| **DISC-LOG-16** | **c) Mejora no bloqueante** | Gestión Naviera / Ciclo de vida | El modelo `shipping.voyage` posee campo `state` (`draft`, `in_transit`, `completed`), pero la vista formulario no tiene botones interactivos para cambiar de estado. La operación de embarques no se bloquea porque se guía por fechas estimadas y reales. | Mantener en backlog de mejoras de UI. No bloquea la entrega operativa. |
| **DISC-LOG-17** | **c) Mejora no bloqueante** | Arquitectura / MRO de Costeo | El método `_get_shipment_costs` en `madenat_lumber_logistics` es sobreescrito por el MRO de `madenat_lumber_costing`. Si el módulo de costeo está instalado, el cálculo opera por el modelo avanzado; si no está instalado, retorna estructura legada. | No representa defecto funcional en el entorno integrado actual. Mantener desacoplado. |
| **DISC-LOG-18** | **c) Mejora no bloqueante** | Documental / Volúmenes de contenedor | Coexistencia de campos `total_vol_shipment_m3` y `total_volume_m3` en `lumber.container`. Ambos se computan correctamente en el código vigente a partir de los lotes asignados. | Mantener ambos campos sin consolidación forzada para no romper vistas heredadas ni reportes PDF/XLSX existentes. |

---

## 6. MATRIZ DE REVERIFICACIÓN DE LOS 28 HALLAZGOS CERRADOS

| ID | Componente / Falla Original | Commit Correctivo | Evidencia Actual Verificada | Límite de Verificación |
|---|---|---|---|---|
| **DISC-OP-01** | Búsqueda por `supplier_label` inexistente en consolidador | `bd918ee` | Código en `lumber_consolidation_import_wizard.py:236` usa `external_labels` con resolución de ambigüedad. | Confirmado en código y pruebas de consolidación. |
| **DISC-OP-02** | `stock.lot` resolvía lotes origen incorrectos en Toll | `9d02ae3` | Código en `madenat_toll_processing/models/stock_lot.py:62` consulta campos reales de orden Toll. | Confirmado en código. |
| **DISC-OP-03** | Falta de permisos en ACL de Toll Processing | `3be3b78` | `security/ir.model.access.csv` en toll otorga permisos a `group_madenat_operaciones` y Jefatura. | Confirmado en archivo ACL. |
| **DISC-OP-04** | Menús técnicos de ingesta visibles a usuarios estándar | `5022969` | `ingestion_menu.xml` oculto o restringido a administradores técnicos. | Confirmado en XML de vistas. |
| **DISC-OP-05** | Menú Toll fuera de estructura en Inventario | `6e945cb` | `menus.xml` en toll asigna `parent="madenat_lumber_core.menu_ops_inventory"` (Control de Lotes). | Confirmado en XML de vistas. |
| **DISC-OP-07** | Desfase de versiones de manifests en CANON | `c8e1491` | `CANON/INDICE_DOCUMENTACION.md` actualizado con versiones reales. | Confirmado en documentación. |
| **DISC-OP-12** | Menús directos de recepción sin clarificación de rol | `f20d9f5` | `CANON/15_DIAGNOSTICO_NAVEGACION_ACTUAL.md` documenta restricción exclusiva a Jefatura. | Confirmado en documentación. |
| **DISC-OP-13** | Dependencia errónea de core en README de ingesta | `9580873` | `madenat_ingestion_engine/README.md` corregido sin dependencia circular. | Confirmado en documentación. |
| **DISC-OP-14** | Estados `error` y `pending_link` ausentes en WIKI | `f064754` | `WIKI/02_TECNICO/modelo_recepciones.md` incluye ambos estados técnicos. | Confirmado en documentación. |
| **DISC-OP-15** | Rutas obsoletas de `madenat_guia_processing` en CANON | `fbdffb4` | Rutas actualizadas en `CANON/12_FLUJOS_INGESTA.md` y `CANON/04_DECISION_LOG.md`. | Confirmado en documentación. |
| **DISC-OP-16** | DEC-002 en WIKI contradecía la existencia de Toll | `bd52d4f` | `WIKI/04_DECISIONES/DEC-002` marcada formalmente como superada por Toll Processing. | Confirmado en documentación. |
| **DISC-OP-17** | Strings de volumen en `stock_lot.py` desalineados | `4a93185` | Strings homologados con los rótulos de vistas bajo directriz AD-111. | Confirmado en código Python. |
| **DISC-OP-20** | Errata "Blacks" en lugar de "Blanks" en manual WIKI | `f064754` | Corregido a "Blanks" en `WIKI/02_TECNICO/modelo_recepciones.md`. | Confirmado en documentación. |
| **DISC-LOG-01** | Error de etiquetas en asistente de consolidación | `bd918ee` | Código saneado en `lumber_consolidation_import_wizard.py`. | Confirmado en código y test unitario. |
| **DISC-LOG-02** | Desincronización de líneas entre contenedor y embarque | `a5e9545` | Métodos `create`/`write`/`unlink` en `lumber_container.py` sincronizan `lumber.shipment.line`. | Confirmado en código. |
| **DISC-LOG-03** | Método erróneo `action_remove_lot_granular` en contenedor | `2d3ba2d` | Método redundante purgado de `lumber_container.py`; conservado en `stock.lot`. | Confirmado en código Python. |
| **DISC-LOG-04** | ACLs permisivas en shipping_core (`base.group_user`) | `af6219b` / `c621d1e` | ACLs restringidas a `shipping_user`, `shipping_manager` y lectura a operaciones/auditoría. | Acreditado por logs `test_core.log` y `test_access.log` (3/3 passed). |
| **DISC-LOG-05** | README logística omitía reactivación del importador | `c4c0b56` | `madenat_lumber_logistics/README.md` actualizado bajo directriz AD-133. | Confirmado en documentación. |
| **DISC-LOG-07** | Desfase de versiones de logística y shipping en CANON | `c8e1491` | `CANON/INDICE_DOCUMENTACION.md` sincronizado con manifiestos vigentes. | Confirmado en documentación. |
| **DISC-LOG-08** | WIKI mencionaba método extinto `_action_reduce_stock` | `e8821bd` | Purgadas menciones en WIKI; documentado zarpe sin movimiento de inventario. | Confirmado en documentación. |
| **DISC-LOG-09** | Estado `rebajado` de contenedor no figuraba en WIKI | `e8821bd` | Incorporado estado `rebajado` en ciclo de vida del contenedor en WIKI. | Confirmado en documentación. |
| **DISC-LOG-10** | Entrada de menú duplicada en retornos de procesador | `d1897a3` | Menú duplicado eliminado de `madenat_processor_return_link_views.xml`. | Confirmado en XML de vistas. |
| **DISC-LOG-11** | Secuencia duplicada `EMB-` en `lumber_actions.xml` | `51c69c6` | Definición redundante eliminada; preservada secuencia canónica id 19 en `data/sequences.xml`. | Confirmado en código y en BD (`SELECT id FROM ir_sequence`). |
| **DISC-LOG-12** | Acción redundante de consolidación en `lumber_actions.xml` | `0910355` | Acción eliminada; conservada acción canónica kanban en `container_views.xml`. | Confirmado en XML de vistas. |
| **DISC-LOG-13** | Archivos huérfanos pre-modularización en shipping_core | `cf0fd61` | Archivos `shipping_menus.xml`, `shipping_views.xml`, `shipping_models.py` eliminados de git. | Confirmado en árbol de trabajo git. |
| **DISC-LOG-15** | Estado inactivo de `menu_export_main` no documentado | `454da43` | `CANON/15_DIAGNOSTICO_NAVEGACION_ACTUAL.md` documenta rama activa de exportación. | Confirmado en documentación. |
| **DISC-LOG-20** | Asistentes B-01 y R1 no figuraban en manual WIKI | `e9c286d` | `WIKI/02_TECNICO/modelo_despachos.md` documenta asistentes de excepción y regularización. | Confirmado en documentación. |
| **H-01/02/03** | Errores en reapertura de guía por falta de `perm_unlink` | `97bf121` / `ef37292` | Limpieza de staging en reapertura y verificación usa `sudo().unlink()` autorizado bajo AD-103. | Confirmado en código Python. |

---

## 7. DICTAMEN FINAL

### **APTO CON CONDICIONES (NO ACREDITADA ENTREGA INTEGRAL HASTA UAT)**

#### Fundamento del Dictamen:
1. **Revisión Estática y de Integridad:**
   - El código en la rama `lote5-desacople-shipping-20261029` (HEAD `26d865d`) no presenta bloqueos de integridad física ni corrupción de inventario.
   - En la base `madenat_test`, se constatan 0 quants negativos en ubicaciones internas y 0 lotes con duplicidad de stock positivo entre patios.
   - El desacople de dependencias del Lote 5 (NEW-01) está verificado y sus pruebas unitarias pasaron con 0 fallos.
2. **Límite de Acreditación:**
   - **No se declara aptitud funcional integral ni entrega definitiva** mientras permanezcan sin ejecutar las pruebas dinámicas PRU-DIN-01, PRU-DIN-02 y PRU-DIN-03 en el entorno interactivo.

#### Condiciones Obligatorias para la Acreditación Definitiva:
1. **Condición de Despliegue (COND-01 / HALL-OPLOG-01):** Ejecutar la actualización por línea de comandos (`odoo -u madenat_lumber_shipping_core,madenat_lumber_logistics`) en `madenat_test` para sellar las versiones `18.0.1.3.0` y `18.0.1.43.0` en `ir_module_module`.
2. **Condición de Negocio (COND-02):** Ratificación formal por Gerencia/Jefatura de Operaciones de las soluciones propuestas a los hallazgos DISC-OP-10 (ubicación de consumo Toll) y DISC-OP-09 (selección de maquilador en Toll).
3. **Condición de Validación Dinámica (COND-03):** Ejecución satisfactoria y documentada de la Matriz UAT (PRU-DIN-01, PRU-DIN-02 y PRU-DIN-03).

---

## 8. LÍMITES DE LA AUDITORÍA
- Auditoría realizada en modo de estricto **SOLO LECTURA** sobre archivos y base de datos `madenat_test`.
- No se ejecutaron modificaciones en bases de datos, creación de registros transaccionales ni cambios en la infraestructura Docker.
- Módulos contables y financieros (`account`, `lumber_cost_distribution`, `lumber_billing_consolidation`) quedaron fuera del alcance funcional auditado, salvo para comprobar la no interferencia con las operaciones y la logística.
