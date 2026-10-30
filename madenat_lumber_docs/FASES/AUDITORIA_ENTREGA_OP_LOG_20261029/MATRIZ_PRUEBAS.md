# MATRIZ DE PRUEBAS Y PLAN DE UAT
## ÁREA: OPERACIONES Y LOGÍSTICA — MADENAT
### Odoo 18 Community Edition

**Fecha:** 2026-10-29  
**Rama:** `lote5-desacople-shipping-20261029` | **HEAD:** `26d865d`  
**Entorno de Referencia:** Base `madenat_test`  
**Estado:** Documento de Preparación (Pruebas Dinámicas **NO EJECUTADAS**)

---

## 1. MATRIZ INTEGRAL DE PRUEBAS UAT (PRU-DIN-01, PRU-DIN-02, PRU-DIN-03)

Esta matriz constituye el protocolo definitivo para la ejecución dinámica de aceptación. Cada prueba describe con precisión sus precondiciones, actores con grupos reales, pasos paso a paso, resultados esperados, evidencia requerida, control de invariantes de stock y criterios explícitos de fallo.

| Caso / ID | Alcance / Escenario | Precondiciones | Actor Real y Grupos Efectivos | Pasos de Ejecución | Resultado Esperado | Evidencia Requerida | Control de Stock / Invariantes | Criterio de Fallo (Bloqueo) |
|---|---|---|---|---|---|---|---|---|
| **PRU-DIN-01** | **Flujo Integral Completo:** Recepción Normal → Maquila con Procesador Distinto → Retorno Parcial → Imputación Documental SV → Consolidación Contenedor → Rebaja Física → Zarpe Normal. | 1. Proveedor de compra (`PROV-MADERA-01`) y Procesador maquilador (`PROC-ASERRADERO-01`) dados de alta como partners distintos.<br>2. Patio `WH/Stock/MARVAL` configurado.<br>3. Motonave, Viaje y Booking disponibles.<br>4. Lote de Madera Verde (SV) recibido. | **Cristhian Elgueta** (ID 8)<br>- `group_madenat_operaciones`<br>- `group_madenat_jefatura_operaciones`<br>- `group_toll_processing_manager`<br>- `group_shipping_manager`<br>- `stock.group_stock_manager` | 1. Ingresar Guía Nacional Normal por Intake; validar físicamente (`done`) asignando destino a `WH/Stock/MARVAL`.<br>2. Crear Orden de Maquila Toll seleccionando explícitamente a `PROC-ASERRADERO-01` (distinto del proveedor) y origen de consumo en `WH/Stock/MARVAL` (DISC-OP-09/10).<br>3. Transferir lote a custodia `WH/Stock/Procesadores/PROC-ASERRADERO-01`.<br>4. Ingresar Guía de Retorno Procesada por volumen parcial con `service_return_confirmation = 'yes'`. Generar 2 tarjas terminadas.<br>5. Abrir *"Rebaja de etiquetas"* (`madenat.sv.imputation.wizard`), imputar las 2 tarjas contra el lote SV padre y aplicar (`action_apply`).<br>6. Asignar 1 tarja a Contenedor en Embarque.<br>7. Ejecutar `action_rebaja_container`.<br>8. Ejecutar `action_set_in_transit` (Zarpe) del embarque. | 1. La recepción genera albarán IN terminado en `WH/Stock/MARVAL`.<br>2. La orden Toll se crea con el partner procesador y consume desde `MARVAL` sin error.<br>3. El envío al procesador mueve el lote a la ubicación de custodia sin generar venta ni merma física.<br>4. La imputación SV pasa a `applied`, calcula saldos documentales y firma SHA-256 sin generar albaranes de salida para el SV (Fase I2).<br>5. La rebaja de contenedor descuenta exactamente una vez la tarja enviándola a `Partners/Customers`.<br>6. El embarque zarpa en estado `in_transit` sin abrir excepción B-01. | - Albarán IN con `state = 'done'`.<br>- Albarán interno a Procesador con `location_dest_id = Procesadores/...`.<br>- Registro `madenat.sv.imputation` con `state = 'applied'`, `snapshot_json` y hash SHA-256.<br>- Albarán OUT de rebaja con `location_dest_id = Partners/Customers`.<br>- Embarque con `state = 'in_transit'`. | 1. **Quant SV:** Permanece intacto en stock físico (no se rebaja en I2).<br>2. **Quant Tarja:** Pasa de `WH/Stock` a `Partners/Customers` exactamente una vez.<br>3. **Quants Internos:** 0 saldos negativos en `WH/Stock` y `MARVAL`. | - Creación de orden Toll forzada al proveedor de compra sin poder elegir procesador.<br>- Consumo de Toll descontando de `WH/Stock` en vez de `MARVAL`.<br>- Generación de albarán de salida física sobre el lote SV al imputar.<br>- Doble movimiento de salida para la tarja exportada. |
| **PRU-DIN-02** | **Excepción de Zarpe B-01, Rolleo de Contenedor y Regularización R1.** | 1. Embarque `EMB-UAT-01` en estado `confirmed` con Contenedor `CONT-UAT-01`.<br>2. Tarja asignada al contenedor pero **sin ejecutar la rebaja física**.<br>3. Segundo embarque `EMB-UAT-02` en estado `draft`/`confirmed`. | **Cristhian Elgueta** (ID 8)<br>- `group_madenat_jefatura_operaciones`<br>- `group_shipping_manager` | 1. En `EMB-UAT-01`, disparar `action_set_in_transit` (Zarpe). El sistema debe advertir contenedores sin rebajar.<br>2. Ingresar motivo de excepción B-01 y confirmar zarpe.<br>3. Verificar que `EMB-UAT-01` pasa a `in_transit` pero abre evento B-01 en auditoría y bloquea la acción de Entrega.<br>4. Intentar rolleo de `CONT-UAT-01` hacia `EMB-UAT-02` mediante `lumber.container.rollover.wizard`.<br>5. Verificar que el asistente de rolleo registra trazabilidad en chatter de ambos embarques.<br>6. Ejecutar asistente de regularización R1 (`lumber.b01.regularization.wizard`) sobre el contenedor pendiente.<br>7. Confirmar regularización y comprobar liberación del bloqueo B-01. | 1. El zarpe no descuenta stock de los contenedores pendientes.<br>2. Se publica mensaje de advertencia B-01 en el chatter.<br>3. El intento de Entrega final queda bloqueado con UserError.<br>4. El rolleo reasigna el contenedor a `EMB-UAT-02` actualizando las líneas de embarque de origen y destino sin duplicar paquetes.<br>5. La regularización R1 genera la rebaja extemporánea y resuelve la excepción B-01. | - Mensaje en chatter de zarpe con emoji `⚠️ Zarpe con excepción B-01`.<br>- Registro `b01_departure_exception` en `madenat_audit_log`.<br>- Mensajes cruzados de rolleo `🔄 Rolleo de Contenedor` en chatter de `EMB-UAT-01` y `EMB-UAT-02`.<br>- Registro `b01_resolution` en `madenat_audit_log`. | 1. El contenedor no rebajado conserva sus quants en ubicación interna hasta que R1 se ejecute.<br>2. Tras rolleo, el stock sigue reservado en el contenedor sin duplicar quants. | - Zarpe que descuenta stock automáticamente sin acción de rebaja.<br>- Zarpe con contenedores pendientes que permite la Entrega comercial directa sin exigir R1.<br>- Rolleo que duplica líneas de tarja o pierde el vínculo con el embarque destino.<br>- Desaparición del motivo en el chatter. |
| **PRU-DIN-03** | **Segregación Efectiva de Funciones en Interfaz Web:** Autonomía Operativa vs. Blindaje de Auditoría. | 1. Usuarios dados de alta y activos en la base.<br>2. Dos sesiones de navegador independientes (o incógnito). | **Usuario A:** Cristhian Elgueta (ID 8)<br>**Usuario B:** Felipe Muñoz (ID 9)<br>- `group_madenat_cost_auditor`<br>- `group_madenat_admin`<br>- `stock.group_stock_manager`<br>*(Sin grupos de Operaciones, Toll ni Shipping)* | 1. **Sesión Cristhian:** Iniciar sesión. Navegar por Consola Intake, Recepciones, Control de Lotes, Toll Processing y Logística Exportación.<br>2. Verificar que no tiene acceso al menú de Ajustes generales de Odoo (`base.group_system`).<br>3. Probar ejecución de validación física y rebaja de contenedor.<br>4. **Sesión Felipe:** Iniciar sesión. Navegar por el menú principal.<br>5. Verificar que **NO visualiza** los menús de Toll Processing (exigen `group_toll_processing_user`).<br>6. Abrir una Recepción y un Embarque. Comprobar que los botones de acción física (`action_validate_physical`, `action_rebaja_container`, `action_set_in_transit`) **no son visibles o están deshabilitados**.<br>7. Acceder a Motonaves y Viajes: comprobar visualización en modo sólo lectura. Intentar crear o borrar un Viaje por interfaz y verificar rechazo por ACL. | 1. Cristhian opera con autonomía completa en los flujos del negocio sin privilegios de administrador del sistema.<br>2. Felipe cuenta con visibilidad para auditoría y costeo pero está impedido de alterar registros operativos, ejecutar movimientos de stock o mutar entidades navieras. | - Acceso concedido a Cristhian en todas las pantallas de su rol.<br>- Ocultamiento efectivo del menú de Ajustes para Cristhian.<br>- Pantalla de navegación de Felipe sin acceso a Toll Processing.<br>- `AccessError` o ausencia de botones de edición/creación para Felipe en modelos operativos y de transporte marítimo. | Ningún movimiento físico de stock puede ser disparado por el usuario de Auditoría. | - Cristhian incapaz de validar recepciones o rebajar contenedores por falta de permisos.<br>- Cristhian con acceso a configuración técnica de Odoo.<br>- Felipe con capacidad de validar recepciones, crear órdenes Toll o rebajar contenedores.<br>- Felipe visualizando menús no autorizados de su rol. |

---

## 2. EVIDENCIA LOCALIZADA EN LA AUDITORÍA PREVIA

A continuación se resume la evidencia ya verificada que sustenta los componentes que serán puestos a prueba dinámicamente:

1. **Evidencia Histórica en Logs Locales:**
   - **Shipping Security:** `/home/viruco/test_core.log` (`TestShippingSecurity`: 3/3 passed).
   - **Acceso Operativo Logística:** `/home/viruco/test_access.log` (`TestShippingAccess`: 3/3 passed).
   - **No Regresión Rolleo y Zarpe:** `/home/viruco/test_rollover21.log` (1/1 passed).
   - **Desacople Botón Buque Lote 5:** `/home/viruco/test_vessel_button.log` (`TestVesselButton`: 3/3 passed).
2. **Evidencia en Base de Datos `madenat_test` (SELECT Solo Lectura):**
   - **Integridad de Quants:** 0 quants negativos en ubicaciones internas; 0 lotes con saldo positivo en múltiples ubicaciones internas.
   - **Trazabilidad en Chatter:** Mensajes 124694 (advertencia B-01) y 136378/136380/136385 (rolleo motivado entre naves con auditoría de usuario y fecha).
   - **Log de Auditoría:** 26 tipos de acción registrados en `madenat_audit_log` (114 lotes creados, 5 rebajas, 10 imputaciones, 4 rolleo de nave, 3 excepciones B-01).

---

## 3. PROTOCOLO DE RECURSOS, AISLAMIENTO Y PROTECCIÓN DEL ENTORNO

Para ejecutar la UAT de forma segura, repetible y sin contaminar datos históricos, se establece el siguiente protocolo de protección:

### 3.1 Política de Respaldo Integral Coherente (BD + Filestore)
Antes de iniciar cualquier prueba dinámica en `madenat_test`:
1. **Respaldo de Base de Datos:**
   ```bash
   docker exec odoo18_db pg_dump -U odoo -d madenat_test -Fc > ~/backups/madenat_test_pre_uat_$(date +%Y%m%d_%H%M).dump
   ```
2. **Respaldo de Filestore:**
   ```bash
   tar -czf ~/backups/filestore_madenat_test_pre_uat_$(date +%Y%m%d_%H%M).tar.gz /var/lib/odoo/.local/share/Odoo/filestore/madenat_test
   ```
   *Ambos respaldos deben ejecutarse de manera coordinada para garantizar la consistencia entre adjuntos documentales (PDFs de guías) y registros PostgreSQL.*

### 3.2 Protección de Registros Históricos
- **Prohibición de Modificación de Datos Preexistentes:** Las pruebas dinámicas no deben editar, reabrir ni eliminar las 9 recepciones, 13 guías procesadas ni 21 embarques existentes en `madenat_test`.
- **Nomenclatura Estricta de Datos de Prueba:** Todo registro creado durante la UAT debe usar el prefijo identificable `UAT-20261029-` (ej. Proveedor `PROV-UAT-01`, Guía `GUIA-UAT-001`, Embarque `EMB-UAT-01`, Contenedor `CONT-UAT-01`).

### 3.3 Principio de No Reversión por Borrado Directo
- En Odoo 18 CE, los movimientos de stock en estado `done` generan quants físicos inmutables. **Está estrictamente prohibido intentar revertir albaranes terminados mediante eliminación directa (SQL DELETE o perm_unlink)**.
- Todo retorno o ajuste de material durante o después de la UAT debe ejecutarse a través de los mecanismos formales del sistema (asistente de retorno nativo `stock.return.picking`, reversa autorizada de rebaja `action_reverse_rebaja` o desvinculación formal).

### 3.4 Justificación de Aislamiento y Base Temporal (Opción Recomendada)
- **Justificación:** Si se desea probar escenarios destructivos o flujos de contingencia extrema sin dejar registros transaccionales en la base operativa de validación `madenat_test`, se recomienda crear una base temporal duplicada.
- **Procedimiento de Creación:**
  ```bash
  docker exec odoo18_db createdb -U odoo -T madenat_test madenat_uat_temp
  ```
- **Plan de Limpieza:** Al concluir las pruebas y registrar las evidencias, la base temporal debe eliminarse de inmediato:
  ```bash
  docker exec odoo18_db dropdb -U odoo madenat_uat_temp
  ```
  *(Esta acción requiere autorización previa del responsable del entorno).*
