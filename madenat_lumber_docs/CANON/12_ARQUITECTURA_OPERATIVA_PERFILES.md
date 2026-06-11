# CANON/12_ARQUITECTURA_OPERATIVA_PERFILES — Arquitectura Operativa por Roles
## Proyecto: MADENAT Lumber — Odoo 18 CE
## Fecha: 2026-06-05
## Estado: DOCUMENTO CANÓNICO — Arquitectura operativa por perfiles
## Ref: CANON/00, CANON/01, CANON/04, CANON/08, Módulos activos

---

# 1. VISIÓN GENERAL DE LA OPERACIÓN

## 1.1 Flujo completo desde la operación hasta la gerencia

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        FLUJO OPERATIVO MADENAT                          │
│                                                                         │
│  [INGRESO]    [STAGING]     [STOCK]    [EMBARQUE]   [COSTEO]   [CIERRE] │
│                                                                         │
│  PDF/Excel ──► Gate 0 ──► Gate 1 ──► Gate 2 ──► Gate 3 ──► stock.lot   │
│       │                                │                                │
│       │   OPERACIONES                  │   OPERACIONES                  │
│       │   • Carga documentos           │   • Verifica dimensiones       │
│       │   • Confirma staging           │   • Corrige nominales          │
│       │   • Asigna supplier/product    │   • Aprueba análisis comercial │
│       │                                │                                │
│       └── stock.lot ◄──────────────────┘                                │
│                │                                                        │
│                │   COSTOS / AUDITORÍA                                   │
│                │   • Asigna wood_cost_usd por lote                      │
│                │   • Registra cost_line_ids adicionales                 │
│                │   • Crea lumber.cost.distribution                      │
│                │   • Ejecuta prorrateo y verifica totales               │
│                │                                                        │
│                ├──► CONTENEDOR ──► EMBARQUE                             │
│                │         │                                              │
│                │         │   OPERACIONES                                │
│                │         │   • Arma contenedores                        │
│                │         │   • Confirma carga                           │
│                │         │   • Zarpa embarque                           │
│                │         │                                              │
│                │         │   COSTOS / AUDITORÍA                         │
│                │         │   • Agrega costos logísticos al embarque     │
│                │         │   • Distribuye costos a lotes                │
│                │         │                                              │
│                │   CONTABILIDAD                                         │
│                │   • Conciliación de recepción vs factura               │
│                │   • Validación de landed costs                         │
│                │   • Preparación de account.move (Fase D)               │
│                │                                                        │
│                └──► GERENCIA                                            │
│                     • Dashboard de márgenes                             │
│                     • Trazabilidad end-to-end                           │
│                     • KPIs de rentabilidad por embarque/producto        │
└─────────────────────────────────────────────────────────────────────────┘
```

## 1.2 Lógica de control por perfiles

| Perfil | Controla | Depende de | Responsabilidad principal |
|--------|----------|------------|---------------------------|
| **Operaciones** | Datos físicos, staging, stock, contenedores, embarques | Costos asigna wood_cost_usd | Calidad y fidelidad del dato operativo |
| **Costos/Auditoría** | Costos base, costos adicionales, distribución, totales | Operaciones entrega lotes creados | Verdad monetaria del lote y del embarque |
| **Contabilidad** | Conciliación documental, tasa de cambio, landed cost, account.move (futuro) | Costos entrega totales validados | Cumplimiento contable y tributario |
| **Gerencia** | Visión consolidada, márgenes, tendencias, KPIs | Todos los perfiles anteriores | Decisiones de negocio basadas en datos reales |

Cada perfil **no puede avanzar** si el perfil anterior no ha cerrado su etapa. El sistema debe impedir técnicamente que una etapa incompleta permita acciones de la etapa siguiente.

## 1.3 Problema que resuelve esta arquitectura

Actualmente el sistema tiene los modelos y flujos técnicos definidos, pero **no existe una separación clara de responsabilidades operativas por rol**. Esto genera:
- Operadores que pueden modificar costos sin validación.
- Costos que no están bloqueados al momento de la conciliación contable.
- Gerencia sin un dashboard consolidado que refleje la realidad operativa.
- Falta de trazabilidad sobre quién aprobó qué y en qué momento.

Esta arquitectura resuelve esos problemas definiendo **qué ve, qué puede hacer, qué valida y qué autoriza cada rol**, con puntos de control obligatorios entre etapas.

---

# 2. MAPA POR PERFILES

## 2.1 PERFIL: OPERACIONES

| Aspecto | Definición |
|---------|------------|
| **Objetivo del rol** | Garantizar que los datos físicos de la madera ingresen correctamente al sistema, desde el documento origen hasta el stock, y desde el stock hasta el embarque. |
| **Qué ve al entrar** | Dashboard de recepciones pendientes, estado de Gates, lotes en inventario sin asignar, contenedores en carga, embarques en borrador. |
| **Qué puede hacer** | Crear recepciones, cargar documentos, ejecutar Gates 0-2, editar staging, corregir dimensiones, confirmar Gate 3 (creación de stock), crear/editar contenedores, asignar lotes a contenedores, confirmar embarque, zarpar. |
| **Qué valida** | Consistencia documento vs staging, dimensiones dentro de tolerancia, producto y subproducto válidos, reglas de exportación aplicadas, contenedores sellados antes de zarpe. |
| **Qué autoriza** | Confirmación de recepción, creación de `stock.lot`, asignación de lotes a contenedores, zarpe de embarque. |
| **Qué bloquea** | No puede modificar `wood_cost_usd` ni costos. No puede tocar tasas de cambio. No puede modificar totales contables. No puede revertir un embarque ya zarpado sin autorización de gerencia. |
| **KPI que debe observar** | Lotes ingresados vs pendientes, tiempo promedio staging→stock, contenedores armados vs capacidad, eficiencia de cubicación por embarque. |

### Permisos específicos de Operaciones

| Modelo | Crear | Leer | Editar | Eliminar |
|--------|-------|------|--------|----------|
| `lumber.reception` | ✅ | ✅ | ✅ (solo draft/verify) | ❌ |
| `lumber.reception.line` | ✅ | ✅ | ✅ (solo en staging) | ❌ |
| `stock.lot` | ❌ (solo vía Gate 3) | ✅ | ✅ (datos físicos, NO costos) | ❌ |
| `lumber.container` | ✅ | ✅ | ✅ | ❌ |
| `lumber.export.shipment` | ✅ | ✅ | ✅ (draft/confirmed) | ❌ |
| `stock.lot.cost.line` | ❌ | ✅ | ❌ | ❌ |
| `lumber.cost.distribution` | ❌ | ✅ | ❌ | ❌ |
| `lumber.export.formula` | ❌ | ✅ | ❌ | ❌ |
| `lumber.ingestion.format` | ❌ | ✅ | ❌ | ❌ |

### Validaciones previas obligatorias

1. **Antes de Gate 3:** todas las líneas de staging deben tener producto, subproducto, dimensiones completas y regla de exportación asignada.
2. **Antes de asignar lote a contenedor:** el lote debe tener `wood_cost_usd > 0` (asignado por Costos). El sistema debe advertir si es 0.
3. **Antes de zarpar:** todos los contenedores deben estar en estado `loaded` o `sealed`. El sistema bloquea el zarpe si hay contenedores `empty` o `loading`.
4. **Antes de confirmar embarque:** debe existir booking_reference y vessel_id.

---

## 2.2 PERFIL: COSTOS / AUDITORÍA

| Aspecto | Definición |
|---------|------------|
| **Objetivo del rol** | Garantizar la integridad monetaria de cada lote y cada embarque. Ser la fuente única de verdad del costo de la madera y los costos logísticos asociados. |
| **Qué ve al entrar** | Dashboard de lotes sin costo asignado, lotes con costo incompleto, expedientes de liquidación pendientes, embarques con costos sin distribuir, alertas de margen negativo. |
| **Qué puede hacer** | Asignar `wood_cost_usd` por lote, crear `stock.lot.cost.line` individuales, crear `lumber.cost.distribution`, ejecutar `action_apply_costs()`, revertir distribuciones, agregar costos al embarque y distribuirlos. |
| **Qué valida** | Que todo lote en inventario tenga `wood_cost_usd > 0`, que los totales de distribución coincidan con el monto origen, que no haya duplicidad de costos, que los márgenes calculados sean consistentes. |
| **Qué autoriza** | Cierre de costo por lote, cierre de costo por embarque, liberación de lotes para asignación a contenedores (implícito al asignar costo base). |
| **Qué bloquea** | No puede modificar datos físicos del lote (dimensiones, piezas). No puede modificar el estado del embarque. No puede modificar datos de recepción. No puede crear ni modificar contenedores. |
| **KPI que debe observar** | % lotes con costo asignado, costo promedio por m³ por especie, costo promedio por MBF, % costos adicionales sobre costo base, lotes con margen proyectado negativo. |

### Permisos específicos de Costos/Auditoría

| Modelo | Crear | Leer | Editar | Eliminar |
|--------|-------|------|--------|----------|
| `stock.lot` (campos monetarios) | ❌ | ✅ | ✅ (solo wood_cost_usd y cost_line_ids) | ❌ |
| `stock.lot.cost.line` | ✅ | ✅ | ✅ | ✅ |
| `lumber.cost.distribution` | ✅ | ✅ | ✅ | ✅ (en draft) |
| `lumber.cost.distribution.line` | ✅ | ✅ | ✅ | ✅ |
| `lumber.reception` | ❌ | ✅ | ❌ | ❌ |
| `lumber.export.shipment` (costos) | ❌ | ✅ | ✅ (solo cost_line_ids) | ❌ |
| `lumber.shipment.cost.line` | ✅ | ✅ | ✅ | ✅ |

### Controles del perfil de Costos

1. **wood_cost_usd no puede ser 0 para un lote en stock.** El sistema debe alertar si hay lotes sin costo al intentar asignarlos a un contenedor.
2. **La distribución de costos debe ser trazable:** cada `stock.lot.cost.line` debe registrar `source_shipment_cost_line_id` o `source_distribution_line_id` para trazabilidad inversa.
3. **Protección de lotes facturados:** el sistema ya tiene regla de que lotes facturados no permiten modificar costos (CANON/08). Esto debe reforzarse con permisos.
4. **Reversibilidad controlada:** `action_reverse_costs()` debe requerir pertenencia al grupo de Costos y solo si el lote no está facturado.

---

## 2.3 PERFIL: CONTABILIDAD

| Aspecto | Definición |
|---------|------------|
| **Objetivo del rol** | Verificar la consistencia contable entre recepciones, costos, embarques y facturación. Preparar la integración con `account.move` (Fase D). |
| **Qué ve al entrar** | Panel de conciliación: recepciones vs facturas de proveedor, landed costs consolidados, tasas de cambio aplicadas, embarques facturados vs no facturados. |
| **Qué puede hacer** | Verificar y ajustar la tasa de cambio (`exchange_rate` en `lumber.reception`), conciliar montos CLP/USD de recepción, revisar landed costs antes del cierre contable, validar que todo costo esté respaldado por documento. |
| **Qué valida** | Que `total_amount_clp` y `total_amount_usd` de la recepción coincidan con la factura del proveedor. Que la suma de landed costs coincida con los documentos de respaldo. Que la tasa de cambio aplicada sea la correcta. |
| **Qué autoriza** | Cierre contable de recepción, validación de landed costs para contabilidad, preparación de base para `account.move`. |
| **Qué bloquea** | No puede modificar datos operativos. No puede modificar costos unitarios de lote. No puede crear/modificar embarques. Solo lectura sobre la operación. |
| **KPI que debe observar** | Recepciones conciliadas vs pendientes, diferencia cambiaria acumulada, landed costs pendientes de contabilizar, tasa de cambio promedio del período. |

### Permisos específicos de Contabilidad

| Modelo | Crear | Leer | Editar | Eliminar |
|--------|-------|------|--------|----------|
| `lumber.reception` (campos contables) | ❌ | ✅ | ✅ (exchange_rate, total_amount_clp) | ❌ |
| `stock.lot` | ❌ | ✅ | ❌ | ❌ |
| `stock.lot.cost.line` | ❌ | ✅ | ❌ | ❌ |
| `lumber.cost.distribution` | ❌ | ✅ | ✅ (validación contable) | ❌ |
| `lumber.export.shipment` | ❌ | ✅ | ❌ | ❌ |
| `lumber.billing.consolidation` | ❌ | ✅ | ✅ (validación) | ❌ |
| `account.move` (Fase D) | ✅ | ✅ | ✅ | ❌ |

### Dependencias hacia Contabilidad

- **Costos debe cerrar** la asignación de `wood_cost_usd` y `cost_line_ids` antes de que Contabilidad pueda validar.
- **Operaciones debe cerrar** el embarque (zarpe) antes de que Contabilidad pueda conciliar costos logísticos.
- **Facturación (billing)** debe generar la consolidación antes del cierre contable final.

---

## 2.4 PERFIL: GERENCIA

| Aspecto | Definición |
|---------|------------|
| **Objetivo del rol** | Tener visibilidad completa y en tiempo real del negocio: qué entró, cuánto costó, a qué precio se vendió, qué margen generó, por embarque, por cliente, por especie. |
| **Qué ve al entrar** | Dashboard gerencial con KPIs consolidados: rentabilidad por embarque, márgenes por producto/cliente, eficiencia operativa, estado documental de embarques, trazabilidad end-to-end. |
| **Qué puede hacer** | Visualizar todo. Aprobar acciones excepcionales: reapertura de recepción cerrada, cancelación de embarque zarpado, ajustes de inventario. |
| **Qué valida** | Que los márgenes estén dentro de lo esperado. Que los tiempos operativos estén en meta. Que no haya lotes huérfanos o sin trazabilidad. |
| **Qué autoriza** | Reversiones excepcionales, ajustes manuales de inventario, cambios de estado forzados, aprobación de cierre de período. |
| **Qué bloquea** | Ningún bloqueo, pero toda acción excepcional debe quedar registrada en `madenat.audit.log` con justificación. |
| **KPI que debe observar** | Ver sección 4.4. |

### Permisos específicos de Gerencia

| Modelo | Crear | Leer | Editar | Eliminar |
|--------|-------|------|--------|----------|
| Todos los modelos | ❌ (salvo excepciones) | ✅ | ❌ (salvo autorizaciones) | ❌ (salvo autorizaciones) |
| `madenat.audit.log` | ❌ (automático) | ✅ | ❌ | ❌ |
| `lumber.reception` (reapertura) | ❌ | ✅ | ✅ (solo reapertura forzada) | ❌ |
| `lumber.export.shipment` (cancelación) | ❌ | ✅ | ✅ (solo cancelación forzada) | ❌ |

---

# 3. PANTALLAS Y FLUJO

## 3.1 Operaciones — Pantallas propuestas

### 3.1.1 Dashboard de Operaciones (Entrada)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `madenat_ops_dashboard` |
| **Tipo** | Kanban + gráficos embebidos |
| **Ubicación** | Menú principal: MADENAT → Operaciones → Dashboard |

**Información que muestra:**

| Widget | Datos | Acción |
|--------|-------|--------|
| Tarjetas de recepción | Recepciones por estado (draft, verify, processed, done) | Clic abre recepción |
| Contador de lotes pendientes | Lotes sin asignar a contenedor | Clic abre lista de lotes |
| Estado de embarques | Embarques por estado con semáforo documental | Clic abre embarque |
| Últimos movimientos | Chatter global de actividad reciente | Solo lectura |
| Alertas | Lotes sin costo, recepciones con Gate 2 abierto > 48h | Clic resuelve |

### 3.1.2 Vista de Recepción (Entrada y Control)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `lumber.reception.form` (ya existe, extender) |
| **Tipo** | Form + líneas + chatter |

**Flujo de navegación:**
1. Operador crea recepción → carga documentos (PDF/Excel).
2. Ejecuta Gate 0 → Gate 1 → Staging poblado.
3. Revisa líneas de staging una por una.
4. Gate 2: análisis comercial. Corrige nominales, asigna subproducto.
5. Gate 3 (CONFIRMAR): snapshot + hash SHA-256 + creación de lotes.

**Validaciones en pantalla:**
- El botón "Gate 3" solo se habilita si todas las líneas pasaron Gate 2.
- Si hay líneas con error, se muestra un contador rojo: "3 líneas con error".
- El wizard de confirmación muestra resumen: N lotes a crear, volumen total, piezas totales.

### 3.1.3 Vista de Lote (Control)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `stock.lot.form.madenat` (extensión de stock.lot) |
| **Tipo** | Form con pestañas |

**Pestañas:**
1. **Datos Físicos:** dimensiones, piezas, volúmenes, producto, subproducto. (Operaciones: editable)
2. **Costos:** `wood_cost_usd`, `total_cost_usd`, `cost_per_m3_usd`, `cost_per_mbf_usd`. (Operaciones: solo lectura)
3. **Costos Detalle:** `cost_line_ids` (Operaciones: solo lectura)
4. **Trazabilidad:** recepción origen, guía, supplier, contenedor, embarque.

### 3.1.4 Vista de Contenedor (Entrada y Control)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `lumber.container.form` (ya existe, extender) |
| **Tipo** | Form + líneas de lote |

**Acciones:**
- "Agregar lotes" → abre wizard de selección de lotes sin contenedor asignado.
- "Confirmar carga" → cambia estado a `loaded`.
- "Sellar" → cambia estado a `sealed`.

**Validación:** no permite agregar un lote que ya está en otro contenedor activo. El sistema filtra lotes con `container_id` vacío.

### 3.1.5 Vista de Embarque (Control y Salida)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `lumber.export.shipment.form` (ya existe, extender) |
| **Tipo** | Form con pestañas |

**Pestañas:**
1. **Generales:** booking, vessel, puertos, fechas.
2. **Contenedores:** lista de contenedores asignados.
3. **Documental:** checklist (booking, VGM, BL, aduana, factura).
4. **Costos:** costos logísticos del embarque (solo lectura para Operaciones).
5. **Comercial:** márgenes, revenue, costos totales (solo lectura).

**Botones de estado:**
- `Confirmar` → validado → `En Tránsito` (Zarpar) → validado → `Entregado`.

### 3.1.6 Vista de Trazabilidad (Control)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `madenat_traceability_view` |
| **Tipo** | Form de solo lectura |

**Flujo visual de trazabilidad:**
```text
Guía/OC → Recepción → Staging → Lote → Contenedor → Embarque → BL → Factura
```

Cada nodo muestra: fecha, usuario, documento asociado, estado. Clic en cualquier nodo abre el registro.

---

## 3.2 Costos/Auditoría — Pantallas propuestas

### 3.2.1 Dashboard de Costos (Entrada)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `madenat_costing_dashboard` |
| **Tipo** | Kanban + gráficos |

**Widgets:**
- Lotes sin `wood_cost_usd` (rojo) → clic asigna costo masivo.
- Lotes con `wood_cost_usd = 0` (naranja) → alerta.
- Distribuciones pendientes de aplicar.
- Costo promedio por m³ del mes (gráfico de línea).
- Distribución de tipos de costo (pastel: flete, puerto, seguro, etc.).

### 3.2.2 Vista de Asignación de Costo Base (Entrada)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `madenat_lot_cost_assignment` (wizard o vista) |
| **Tipo** | Lista + edición inline |

**Funcionalidad:**
- Filtro: lotes en stock sin `wood_cost_usd` o con valor 0.
- Columnas: lote, producto, supplier, volumen, `wood_cost_usd` (editable).
- Acción "Guardar y validar" → asigna costos en lote.

**Regla de negocio:** `wood_cost_usd` debe ser > 0 para todo lote en inventario disponible.

### 3.2.3 Vista de Expediente de Liquidación (Entrada y Control)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `lumber.cost.distribution.form` (ya existe, extender) |
| **Tipo** | Form + líneas |

**Flujo:**
1. Seleccionar origen: booking / container / reception / purchase.
2. Agregar líneas de costo (factura de flete, gastos portuarios, seguro, etc.).
3. Seleccionar método de prorrateo (volume_export, volume_physical, weight, pieces, equal, container).
4. Ejecutar `action_apply_costs()` → inyecta `stock.lot.cost.line` en cada lote.
5. Verificar totales en lote → `total_cost_usd` actualizado.

### 3.2.4 Vista de Costos de Embarque (Entrada y Control)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `lumber.export.shipment.form` (pestaña Costos, modo edición para Costos) |
| **Tipo** | Form + líneas de costo |

- Agregar `lumber.shipment.cost.line`.
- Ejecutar `action_distribute_costs()` → distribuye a lotes del embarque.

### 3.2.5 Vista de Auditoría de Costos (Salida)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `madenat_cost_audit_view` |
| **Tipo** | Tree + Pivot + Graph |

**Columnas:**
lote, producto, wood_cost_usd, Σ cost_line_ids, total_cost_usd, cost_per_m3_usd, cost_per_mbf_usd, embarque, margen_usd, margen_pct.

**Filtros rápidos:**
- Lotes con margen negativo.
- Lotes sin costo adicional.
- Lotes con costo > precio de venta.

---

## 3.3 Contabilidad — Pantallas propuestas

### 3.3.1 Panel de Conciliación (Entrada)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `madenat_accounting_reconciliation` |
| **Tipo** | Tree + Filtros |

**Columnas:**
recepción, supplier, total_amount_clp, total_amount_usd, exchange_rate, factura_proveedor, diferencia, estado_conciliación.

**Estados de conciliación:**
- `pendiente`: recepción sin factura de proveedor cargada.
- `conciliado`: montos coinciden.
- `diferencia`: montos no coinciden, requiere ajuste.

### 3.3.2 Vista de Landed Cost Contable (Control)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `lumber.cost.distribution.form` (pestaña Contabilidad) |
| **Tipo** | Solo lectura + validación |

- Muestra el detalle completo del expediente.
- Botón "Validar para contabilidad" → registra fecha y usuario de validación contable.
- Futuro (Fase D): botón "Generar account.move".

### 3.3.3 Vista de Cierre de Período (Salida)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `madenat_period_close` (wizard) |
| **Tipo** | Wizard de confirmación |

**Validaciones antes del cierre:**
- Todas las recepciones del período en estado `done`.
- Todos los embarques zarpados con costos distribuidos.
- Todos los lotes con `wood_cost_usd > 0`.
- Ninguna conciliación pendiente.

---

## 3.4 Gerencia — Pantallas propuestas

### 3.4.1 Dashboard Gerencial Consolidado (Entrada)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `madenat_executive_dashboard` |
| **Tipo** | Form con widgets embebidos |

**Widgets y KPIs (ver sección 4.4).**

### 3.4.2 Vista de Rentabilidad por Embarque (Salida)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `madenat_shipment_profitability` |
| **Tipo** | Pivot + Graph |

**Filas:** Embarque. **Columnas:** total_revenue_usd, total_cost_usd, gross_margin_usd, gross_margin_pct.

### 3.4.3 Vista de Trazabilidad 360 (Salida)

| Campo | Descripción |
|-------|-------------|
| **Nombre** | `madenat_traceability_360` |
| **Tipo** | Form de solo lectura con gráfico de flujo |

Muestra el recorrido completo de un lote desde la guía hasta la factura, con todos los estados, fechas y usuarios intermedios.

---

# 4. KPI POR PERFIL

## 4.1 KPIs de Operaciones

| KPI | Descripción | Tipo | Frecuencia | Cálculo |
|-----|-------------|------|------------|---------|
| **Recepciones procesadas** | N° de recepciones que pasaron a done en el período | Operativo | Diario/Semanal | COUNT(recepción WHERE state='done' AND fecha_cierre EN período) |
| **Tiempo staging→stock** | Horas promedio desde Gate 0 hasta Gate 3 | Operativo | Semanal | AVG(fecha_gate3 - fecha_gate0) |
| **Lotes creados** | Total de stock.lot creados en el período | Operativo | Diario | COUNT(stock.lot WHERE create_date EN período) |
| **Contenedores armados** | Contenedores en estado loaded/sealed | Operativo | Diario | COUNT(container WHERE state IN ('loaded','sealed')) |
| **Eficiencia de cubicación** | % de volumen de embarque vs volumen físico por embarque | Operativo | Por embarque | (total_volume_m3 / total_nominal_volume_m3) × 100 |
| **Embarques zarpados** | Embarques en estado in_transit o delivered | Operativo | Semanal | COUNT(shipment WHERE state IN ('in_transit','delivered')) |
| **% Documental completado** | Promedio de document_completion de embarques activos | Operativo | Semanal | AVG(document_completion) |

## 4.2 KPIs de Costos/Auditoría

| KPI | Descripción | Tipo | Frecuencia | Cálculo |
|-----|-------------|------|------------|---------|
| **% Lotes con costo asignado** | Lotes con wood_cost_usd > 0 sobre total de lotes en stock | Financiero | Diario | COUNT(lotes con wood_cost>0) / COUNT(total lotes) × 100 |
| **Costo promedio por m³** | Costo total USD / volumen total m³ | Financiero | Semanal | SUM(total_cost_usd) / SUM(volumen_m3) |
| **Costo promedio por MBF** | Costo total USD / volumen total MBF | Financiero | Semanal | SUM(total_cost_usd) / SUM(volumen_mbf) |
| **% Costos adicionales** | Σ cost_line_ids / wood_cost_usd promedio | Financiero | Semanal | AVG(costos_adicionales / wood_cost_usd) × 100 |
| **Expedientes pendientes** | Distribuciones en estado draft o pending | Operativo | Diario | COUNT(distribution WHERE state='draft') |
| **Lotes con margen proyectado negativo** | Lotes cuyo cost_per_mbf_usd > sale_price_usd_per_mbf | Financiero | Semanal | COUNT(lotes WHERE margen < 0) |
| **Tiempo asignación costo** | Días desde creación del lote hasta asignación de wood_cost_usd | Operativo | Semanal | AVG(fecha_costo - fecha_creacion_lote) |

## 4.3 KPIs de Contabilidad

| KPI | Descripción | Tipo | Frecuencia | Cálculo |
|-----|-------------|------|------------|---------|
| **Recepciones conciliadas** | % de recepciones con factura de proveedor verificada | Contable | Mensual | COUNT(conciliado) / COUNT(total) × 100 |
| **Diferencia cambiaria** | Suma de diferencias entre USD calculado y USD facturado | Contable | Mensual | SUM(abs(total_amount_usd - factura_usd)) |
| **Landed costs contabilizados** | Expedientes con validación contable completada | Contable | Mensual | COUNT(distribución WHERE validada_contabilidad=true) |
| **Tasa de cambio promedio** | Promedio ponderado de exchange_rate del período | Contable | Mensual | AVG(exchange_rate) ponderado por monto |
| **Embarques pendientes de facturación** | Embarques delivered sin invoice_issued | Contable | Semanal | COUNT(shipment WHERE state='delivered' AND invoice_issued=false) |

## 4.4 KPIs de Gerencia

| KPI | Descripción | Tipo | Frecuencia | Cálculo |
|-----|-------------|------|------------|---------|
| **Margen bruto consolidado** | (Revenue - Total Cost) / Revenue × 100 | Gerencial | Mensual | SUM(margin_usd) / SUM(sale_amount_usd) × 100 |
| **Margen por embarque** | Margen bruto de cada embarque en USD y % | Gerencial | Por embarque | gross_margin_usd, gross_margin_pct |
| **Revenue total** | Suma de ingresos por venta de todos los lotes | Gerencial | Mensual | SUM(sale_amount_usd) |
| **Costo total** | Suma de wood_cost_usd + todos los costos adicionales | Gerencial | Mensual | SUM(total_cost_usd) |
| **Volumen exportado** | m³ y MBF exportados en el período | Gerencial | Mensual | SUM(vol_shipment_m3), SUM(volumen_mbf) |
| **Eficiencia operativa** | Tiempo promedio desde recepción hasta zarpe | Gerencial | Mensual | AVG(fecha_zarpe - fecha_recepcion) |
| **Top 5 clientes por margen** | Clientes con mayor margen bruto | Gerencial | Mensual | GROUP BY customer ORDER BY margin DESC LIMIT 5 |
| **Top 5 productos por rentabilidad** | Productos con mayor margen % | Gerencial | Mensual | GROUP BY product ORDER BY margin_pct DESC LIMIT 5 |
| **Tendencia de márgenes** | Evolución del margen bruto mes a mes | Gerencial | Mensual | Serie temporal de gross_margin_pct |

### KPIs futuros (dependen de Fase D y data no consolidada aún)

| KPI | Dependencia |
|-----|-------------|
| **Costo contable real** (con valuation layers) | Fase D — Integración `stock.valuation.layer` |
| **Asiento contable automático** | Fase D — `account.move` desde landed costs |
| **Flujo de caja proyectado** | Fase futura — cuentas por pagar/cobrar integradas |

---

# 5. PERMISOS Y CONTROL

## 5.1 Grupos de seguridad propuestos

| Grupo Odoo | Perfil | Módulo |
|------------|--------|--------|
| `group_madenat_operaciones` | Operaciones | `madenat_lumber_core` |
| `group_madenat_costos` | Costos / Auditoría | `madenat_lumber_core` |
| `group_madenat_contabilidad` | Contabilidad | `madenat_lumber_core` |
| `group_madenat_gerencia` | Gerencia | `madenat_lumber_core` |

### Herencia de grupos Odoo estándar:

| Grupo MADENAT | Hereda de | Justificación |
|---------------|-----------|---------------|
| `group_madenat_operaciones` | `stock.group_stock_user` | Necesita crear/editar movimientos de stock |
| `group_madenat_costos` | `base.group_user` | Acceso a modelos de costo, sin permisos de stock write |
| `group_madenat_contabilidad` | `account.group_account_invoice` | Acceso a modelos contables |
| `group_madenat_gerencia` | `base.group_user` | Solo lectura con permisos de autorización excepcional |

## 5.2 Matriz de permisos por modelo y rol

| Modelo | Operaciones | Costos | Contabilidad | Gerencia |
|--------|-------------|--------|--------------|----------|
| `lumber.reception` | RW (draft/verify) | R | RW (campos contables) | R (reapertura) |
| `lumber.reception.line` | RW | R | R | R |
| `stock.lot` | RW (datos físicos) | RW (campos monetarios) | R | R (ajuste excepcional) |
| `stock.lot.cost.line` | R | CRUD | R | R |
| `lumber.cost.distribution` | R | CRUD | RW (validación) | R |
| `lumber.cost.distribution.line` | R | CRUD | R | R |
| `lumber.container` | CRUD | R | R | R (ajuste excepcional) |
| `lumber.export.shipment` | CRUD | RW (costos) | R | R (cancelación forzada) |
| `lumber.shipment.cost.line` | R | CRUD | R | R |
| `lumber.export.formula` | R | R (admin) | R | R |
| `lumber.ingestion.format` | R | R (admin) | R | R |
| `lumber.billing.consolidation` | R | R | RW | R |
| `madenat.audit.log` | C (automático) | C (automático) | C (automático) | R |
| `account.move` (Fase D) | - | - | CRUD | R |

## 5.3 Acciones restringidas

| Acción | Restricción | Quién puede | Condición |
|--------|-------------|-------------|-----------|
| Modificar `wood_cost_usd` después de facturación | BLOQUEADO | Nadie | Lote con invoice asociado |
| Cancelar embarque zarpado | RESTRINGIDO | Gerencia | Requiere justificación en audit log |
| Reabrir recepción cerrada (done) | RESTRINGIDO | Gerencia | Revierte stock, registra en audit log |
| Eliminar `stock.lot.cost.line` | RESTRINGIDO | Costos | Solo si lote no está facturado y vía `action_reverse_costs()` |
| Modificar dimensiones de lote en stock | RESTRINGIDO | Operaciones (solo ajuste justificado) | Requiere registro en audit log |
| Crear `account.move` manual | RESTRINGIDO | Contabilidad | Solo después de validación de landed costs |

## 5.4 Trazabilidad de cambios y aprobaciones

### Modelo `madenat.audit.log` (ya existe) debe registrar:

| Evento | Datos registrados |
|--------|-------------------|
| Gate 3 ejecutado | recepción_id, usuario, timestamp, N lotes creados, hash SHA-256 |
| Asignación de `wood_cost_usd` | lote_id, valor_anterior, valor_nuevo, usuario, timestamp |
| Distribución de costos aplicada | distribución_id, N líneas creadas, usuario, timestamp |
| Zarpe de embarque | embarque_id, usuario, timestamp, N contenedores |
| Reapertura forzada | registro_id, motivo, usuario, timestamp |
| Cancelación forzada | registro_id, motivo, usuario, timestamp |
| Ajuste de inventario | lote_id, campo_modificado, valor_anterior, valor_nuevo, usuario |

### Regla de oro de trazabilidad:
> Todo cambio que afecte costo, stock o estado debe generar una entrada en `madenat.audit.log` con usuario, timestamp, valor anterior y valor nuevo.

---

# 6. SECUENCIA DE VALIDACIÓN

## 6.1 Flujo de validación entre perfiles

```text
┌──────────────────────────────────────────────────────────────────────┐
│                    SECUENCIA DE VALIDACIÓN                           │
│                                                                      │
│  [1] OPERACIONES: Ingesta + Staging                                 │
│       │                                                              │
│       ├── Gate 0: formato, integridad                               │
│       ├── Gate 1: consistencia documental                            │
│       ├── Gate 2: análisis comercial, dimensiones, tolerancias       │
│       ├── Gate 3: snapshot + SHA-256 + creación de stock.lot         │
│       │                                                              │
│       ▼                                                              │
│  [2] COSTOS: Asignación monetaria                                    │
│       │                                                              │
│       ├── wood_cost_usd > 0 para cada lote                          │
│       ├── cost_line_ids (costos adicionales)                         │
│       ├── lumber.cost.distribution aplicado                          │
│       │                                                              │
│       ▼                                                              │
│  [3] OPERACIONES: Logística de exportación                           │
│       │                                                              │
│       ├── Lotes → Contenedores (solo lotes con costo asignado)       │
│       ├── Contenedores → Embarque                                    │
│       ├── Confirmar → Zarpar (solo con contenedores sealed/loaded)   │
│       │                                                              │
│       ▼                                                              │
│  [4] COSTOS: Costos logísticos del embarque                          │
│       │                                                              │
│       ├── lumber.shipment.cost.line agregadas                        │
│       ├── action_distribute_costs() → inyecta en lotes              │
│       │                                                              │
│       ▼                                                              │
│  [5] CONTABILIDAD: Conciliación y validación                         │
│       │                                                              │
│       ├── Conciliación recepción vs factura proveedor                │
│       ├── Validación de landed costs                                 │
│       ├── Cierre contable del período                                │
│       │                                                              │
│       ▼                                                              │
│  [6] GERENCIA: Dashboard y decisiones                                │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## 6.2 Puntos de control obligatorios (GATES DE NEGOCIO)

| Gate de Negocio | Validación | ¿Quién ejecuta? | ¿Bloquea qué? |
|-----------------|------------|-----------------|---------------|
| **GB-1** | Todo lote en inventario debe tener `product_id`, dimensiones completas y regla de exportación | Operaciones (Gate 2) | Paso a Gate 3 |
| **GB-2** | Todo lote creado debe tener `wood_cost_usd > 0` | Costos | Asignación a contenedor |
| **GB-3** | Todo contenedor debe estar `loaded` o `sealed` | Operaciones | Zarpe del embarque |
| **GB-4** | Todo embarque zarpado debe tener costos logísticos distribuidos | Costos | Cierre contable |
| **GB-5** | Toda recepción debe tener factura de proveedor conciliada | Contabilidad | Cierre de período |
| **GB-6** | Cierre de período validado | Contabilidad → Gerencia | Dashboard gerencial refleja período cerrado |

## 6.3 Cómo evitar cierres sin evidencia

1. **Snapshots en Gate 3:** antes de crear lotes, el sistema captura snapshot completo del staging y calcula hash SHA-256. Esto se almacena en `audit_snapshot` y `audit_hash` de `lumber.reception`.
2. **Trazabilidad en costos:** cada `stock.lot.cost.line` referencia su origen (`source_shipment_cost_line_id` o `source_distribution_line_id`).
3. **Log de auditoría obligatorio:** todo cambio de estado, asignación de costo, zarpe y cierre debe generar `madenat.audit.log`.
4. **Validación contable explícita:** el expediente de liquidación debe tener un campo `validated_by_accounting` (boolean + timestamp + user) que solo Contabilidad puede activar.
5. **Dashboard gerencial con modo "período cerrado":** el dashboard diferencia entre datos de período abierto (sujetos a cambio) y período cerrado (inmutables).

---

# 7. RECOMENDACIÓN DE IMPLEMENTACIÓN

## 7.1 Ruta incremental

### Fase 1: Permisos y grupos de seguridad (2-3 días)
- Crear los 4 grupos de seguridad en `madenat_lumber_core/security/`.
- Actualizar `ir.model.access.csv` con la matriz de permisos definida en la sección 5.2.
- **Depende de:** nada. Es la base sobre la que se construye todo lo demás.
- **Entregable:** los roles ya no pueden hacer acciones fuera de su ámbito.

### Fase 2: Dashboards por perfil (3-5 días)
- Crear vistas de dashboard para cada perfil (sección 3).
- Operaciones: dashboard con recepciones pendientes, lotes sin asignar, embarques activos.
- Costos: dashboard con lotes sin costo, distribuciones pendientes, márgenes negativos.
- Contabilidad: panel de conciliación.
- Gerencia: dashboard consolidado con KPIs.
- **Depende de:** Fase 1 (para filtrar datos según permisos).
- **Entregable:** cada perfil tiene una pantalla de entrada con sus indicadores clave.

### Fase 3: Validaciones y puntos de control (3-4 días)
- Implementar los Gates de Negocio GB-1 a GB-6 (sección 6.2).
- Agregar validaciones en acciones existentes (action_confirm, action_set_in_transit, action_apply_costs).
- Implementar `madenat.audit.log` para los eventos definidos en 5.4.
- **Depende de:** Fase 1.
- **Entregable:** el sistema impide avanzar si no se cumplen las condiciones del gate correspondiente.

### Fase 4: Trazabilidad y auditoría (2-3 días)
- Vista de trazabilidad 360 para gerencia (sección 3.4.3).
- Extensión del modelo `madenat.audit.log` si es necesario.
- Botón "Trazabilidad" en lote y embarque.
- **Depende de:** Fase 3 (los eventos ya se están registrando).
- **Entregable:** trazabilidad completa consultable desde UI.

### Fase 5: KPIs y reportes gerenciales (3-4 días)
- Implementar los KPIs definidos en la sección 4.
- Vistas pivot y graph para rentabilidad por embarque, por cliente, por producto.
- Dashboard gerencial con widgets embebidos.
- **Depende de:** Fase 2 y Fase 4.
- **Entregable:** gerencia ve el negocio completo en tiempo real.

### Fase 6: Integración contable — Fase D del backlog (5-7 días)
- `stock.valuation.layer` automático desde landed costs.
- `account.move` desde `lumber.cost.distribution`.
- Conciliación contable asistida.
- **Depende de:** Fase 3 y Fase 4.
- **Entregable:** contabilidad integrada con Odoo estándar.

## 7.2 Dependencias entre fases

```text
Fase 1 (Permisos)
    │
    ├──► Fase 2 (Dashboards)
    │        │
    │        └──► Fase 5 (KPIs y Reportes)
    │
    ├──► Fase 3 (Validaciones)
    │        │
    │        ├──► Fase 4 (Trazabilidad)
    │        │        │
    │        │        └──► Fase 5 (KPIs)
    │        │
    │        └──► Fase 6 (Contabilidad)
    │
    └──► (Fase 2, 3, 4 pueden ejecutarse en paralelo tras Fase 1)
```

## 7.3 Qué puede implementarse de forma incremental

- **Permisos:** inmediato, no rompe nada, solo restringe.
- **Dashboards:** vistas nuevas, no modifican lógica existente.
- **Validaciones:** se agregan como pre-condiciones en botones existentes. Cada gate puede implementarse y probarse de forma aislada.
- **Trazabilidad:** consumidor de eventos ya registrados. No modifica flujo.
- **KPIs:** consultas SQL/computes nuevos. No modifican escritura.

---

# 8. CONCLUSIÓN EJECUTIVA

## 8.1 Resumen de la arquitectura propuesta

La arquitectura operativa por perfiles de MADENAT define **cuatro roles con responsabilidades, pantallas, KPIs y permisos claramente delimitados**:

| Perfil | Entrada | Control | Salida |
|--------|---------|---------|--------|
| **Operaciones** | Dashboard de recepciones y embarques | Staging, dimensiones, gates físicos | Lotes en stock, embarques zarpados |
| **Costos/Auditoría** | Dashboard de costos pendientes | wood_cost_usd, distribuciones, prorrateos | Costos unitarios por lote y embarque |
| **Contabilidad** | Panel de conciliación | Tasas de cambio, landed costs, facturación | Cierre contable, base para account.move |
| **Gerencia** | Dashboard consolidado | Márgenes, KPIs, trazabilidad 360 | Decisiones basadas en datos reales |

El flujo sigue una **secuencia de validación estricta** con 6 Gates de Negocio que impiden que una etapa avance sin que la anterior esté cerrada y evidenciada.

## 8.2 ¿Es suficiente para ver la operación completa?

**Sí.** Con esta arquitectura implementada, cualquier stakeholder puede:
- Ver el estado real de la operación en tiempo real.
- Identificar cuellos de botella (lotes sin costo, recepciones sin procesar, embarques sin documentación).
- Auditar la trazabilidad completa de cualquier lote.
- Tomar decisiones gerenciales con datos monetarios consolidados y verificados.
- Cumplir con requisitos contables y de auditoría.

## 8.3 Qué faltaría para el diseño técnico detallado

Si se desea pasar al diseño técnico detallado (especificaciones de código, vistas XML, métodos Python), se requiere adicionalmente:

1. **Especificación de vistas Odoo:** XML completo para cada dashboard, formulario y wizard propuesto.
2. **Modelo de datos de `madenat.audit.log`:** campos exactos, relaciones, vistas.
3. **Especificación de computes de KPIs:** lógica de cálculo, depends, store.
4. **Definición de grupos de seguridad en XML:** `madenat_lumber_core/security/madenat_groups.xml`.
5. **Actualización de `ir.model.access.csv`:** matriz completa de permisos con los nuevos grupos.
6. **Especificación de actions y menús:** estructura de menús por perfil.
7. **Casos de prueba funcionales:** tests para cada Gate de Negocio y cada validación.
8. **Runbook de operación por perfil:** manual de usuario para cada rol.

---

## Regla de mantenimiento

Este documento debe actualizarse cuando:
- Se agregue un nuevo perfil o se modifiquen las responsabilidades de uno existente.
- Se implemente un nuevo módulo que afecte el flujo operativo.
- Se modifiquen los Gates de Negocio o la secuencia de validación.
- Se agreguen o modifiquen KPIs gerenciales.
- Cambie la matriz de permisos.

---

*Documento creado: 2026-06-05*
*Versión: 1.0.0*
*Autor: Arquitectura MADENAT — CANON/12*