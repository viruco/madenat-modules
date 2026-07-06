# Auditaría Integral — Consola de Compras Madera Bruta
## `action_madenat_purchase_order` | `purchase.order`
### 2026-06-07 — Consultor Senior Odoo 18 CE

---

# 1. HALLAZGOS TÉCNICOS

## 1.1 Acción `action_madenat_purchase_order` (purchase_order_views_ce.xml:138-156)

| Parámetro | Valor real | Análisis |
|---|---|---|
| `res_model` | `purchase.order` | Correcto |
| `view_mode` | `list,kanban,form,pivot,graph` | **Problema detectado** |
| `search_view_id` | `view_purchase_order_madenat_search` | Correcto, bien diseñada |
| `context` | `{'search_default_state_purchase': 1}` | Correcto: abre en confirmadas |
| `view_ids` | Lista explícita con 5 entradas | Ver detalle abajo |
| `help` | HTML con emoji 🌲 | Correcto, sobrio |

**Desglose de `view_ids`:**

| Modo | view_id apuntado | ¿Es estándar? | Riesgo |
|---|---|---|---|
| `list` | `view_purchase_order_kpis_tree_madenat_pro` | **NO** — standalone, `inherit_id=False` | Sin riesgo |
| `kanban` | `purchase.view_purchase_order_kanban` | **SÍ** — kanban estándar de purchase | **ALTO** — contiene dashboard/KPI retail |
| `form` | `purchase.purchase_order_form` | SÍ — pero heredado por `view_purchase_order_form_lumber` | Bajo — la herencia agrega pestañas de madera |
| `pivot` | `False` (sin view_id) | **SÍ** — Odoo usa vista pivot estándar | **MEDIO** — métricas de retail |
| `graph` | `False` (sin view_id) | **SÍ** — Odoo usa vista graph estándar | **MEDIO** — métricas de retail |

## 1.2 Vista Tree en ejecución: `view_purchase_order_kpis_tree_madenat_pro`

- **Tipo:** `<list>` standalone, sin herencia (`inherit_id=False`)
- **Número de campos visibles por defecto:** **17** (todos con `optional="hide"`)
- **Campos con `optional="hide"` (visibles por defecto):** name, partner_id, lumber_volume_m3, received_volume_m3, pending_volume_m3, amount_total, state, reception_count, percent_completed, partner_ref, monto_recibido_usd, date_order, date_approve, user_id, invoice_status, variance_commercial_physical, total_lots_count
- **Campos invisibles:** `provisional` (invisible="1")
- **Botones:** `action_review_provisional` (condicional a `provisional == False`)
- **Decoraciones:** warning/provisional, success/completado, info/borrador-enviadas, danger/canceladas
- **`sample="1"`:** presente (muestra datos de ejemplo si no hay registros)

## 1.3 `retrieve_dashboard`

- **En la tree view `view_purchase_order_kpis_tree_madenat_pro`:** NO se llama. Es un `<list>` puro, no un dashboard.
- **En el kanban `purchase.view_purchase_order_kanban`:** SÍ se llama. El kanban estándar de purchase en Odoo 18 CE es un dashboard kanban que invoca `retrieve_dashboard` para mostrar KPIs superiores (RfQ count, Purchase Orders count, valor promedio, actividad reciente, plazos, etc.).
- **Conclusión:** `retrieve_dashboard` NO se llama en la vista principal (list), pero SÍ se llama cuando el usuario cambia manualmente a vista kanban. Esto significa que el switch a kanban **arrastra residuos de KPI retail**.

## 1.4 Vistas heredadas residuales

Existe una vista heredada en `purchase_order_views.xml`:

```
view_purchase_order_list_lumber
  → inherit_id = purchase.purchase_order_view_tree (estándar)
  → agrega campos de madera después de `name`
```

Esta vista:
- **NO es usada** por `action_madenat_purchase_order` (la acción usa `view_ids` explícitos que apuntan a la standalone)
- **NO contamina** la consola principal
- Es código legacy que **debería eliminarse o marcarse como deprecado**

## 1.5 Vista `purchase_tracking_views.xml` (acción separada)

La acción `action_purchase_tracking` usa:
- `view_id`: `view_purchase_tracking_tree` (tree simple con 7 columnas)
- `search_view_id`: `purchase.view_purchase_order_filter` (¡estándar de purchase!)
- `context`: `{'search_default_current_year': 1}`

**Problema detectado:** Esta acción de seguimiento todavía usa el search view estándar de purchase. Debería usar el search view de madera o uno propio.

---

# 2. CAUSA RAÍZ

El problema NO está en la tree view (que es standalone y correcta en su intención). El problema tiene **tres capas**:

## Capa 1 — Exceso de columnas visibles por defecto
Todas las 17 columnas están marcadas `optional="hide"`, lo que significa que son visibles por defecto. La intención del desarrollador (visible en el comentario XML "COLUMNAS OPCIONALES (Personalizar)") era que los campos 9-17 estuvieran ocultos por defecto (`optional="show"`), pero se usó `optional="hide"` incorrectamente en todas.

**Esto produce una consola de 17 columnas visibles. Invendible para uso ejecutivo.**

## Capa 2 — Kanban/pivot/graph heredan vistas estándar con KPI retail
- El kanban (`purchase.view_purchase_order_kanban`) es el dashboard kanban estándar que llama `retrieve_dashboard` y muestra KPIs genéricos de retail.
- Pivot y graph sin view_id explícito también heredan comportamiento estándar.
- Aunque el usuario trabaje en modo lista 95% del tiempo, cambiar a kanban muestra KPIs que no tienen sentido para madera.

## Capa 3 — Orden de columnas subóptimo
`name` (OC) antes que `partner_id` (Proveedor) invierte la jerarquía natural del negocio maderero: cada fila debe leerse "Proveedor X tiene la OC Y".

---

# 3. DIAGNÓSTICO FUNCIONAL (por perfil)

## 3.1 Gerencia de Abastecimiento

| Necesidad | ¿Está? | Columna |
|---|---|---|
| Ver proveedor primero | NO — está segundo | partner_id |
| Volumen contratado | SÍ | lumber_volume_m3 |
| Volumen recibido | SÍ | received_volume_m3 |
| Volumen pendiente | SÍ | pending_volume_m3 |
| % completado | SÍ pero sobra como columna fija | percent_completed |
| Compromiso financiero total | SÍ | amount_total |
| Lo recibido en USD | SÍ | monto_recibido_usd |
| **Sobra:** user_id (comprador interno) | **FUERA** | user_id |
| **Sobra:** total_lots_count | **FUERA** | total_lots_count |
| **Sobra:** variance detalle fino | **FUERA** | variance_commercial_physical |
| **Sobra:** reception_count en columna | **OPCIONAL** | reception_count |

## 3.2 Finanzas / Auditoría

| Necesidad | ¿Está? | Columna |
|---|---|---|
| Monto total contratado | SÍ | amount_total |
| Monto recibido | SÍ | monto_recibido_usd |
| Estado de facturación | SÍ | invoice_status |
| Estado de la OC | SÍ | state |
| Proveedor | SÍ | partner_id |
| **Sobra:** campos de volumen | **No sobran** — necesitan ver qué volumen respalda cada monto |
| **Sobra:** user_id | **FUERA** | user_id |

## 3.3 Operación de Recepción

| Necesidad | ¿Está? | Columna |
|---|---|---|
| Proveedor + ref | SÍ | partner_id, partner_ref |
| OC | SÍ | name |
| Volumen contratado vs recibido vs pendiente | SÍ | lumber_volume_m3, received_volume_m3, pending_volume_m3 |
| % completado | SÍ | percent_completed |
| Guías recibidas | SÍ | reception_count |
| **Sobra:** amount_total | **No sobra** — es referencia |
| **Sobra:** monto_recibido_usd | **No sobra** — es referencia |
| **Sobra:** user_id | **FUERA** | user_id |
| **Falta:** desvío visible al recibir | **OPCIONAL** | variance_commercial_physical |

## 3.4 Administración

| Necesidad | ¿Está? | Columna |
|---|---|---|
| Estado general por OC | SÍ | state |
| Fechas clave | SÍ pero deben ser opcionales | date_order, date_approve |
| Facturación pendiente | SÍ | invoice_status |
| **Sobra:** demasiadas columnas de volumen | Reducir a las 3 esenciales | |

**Conclusión funcional:** Los 4 perfiles coinciden en que el núcleo visible debe ser: **Proveedor → Ref → OC → Volumen contratado → Recibido → Pendiente → Monto total → Monto recibido → Estado**. Todo lo demás debe ser opcional.

---

# 4. DIAGNÓSTICO VISUAL

## 4.1 Jerarquía actual (incorrecta)

```
OC → Proveedor → Contratado → Recibido → Pendiente → Total $$ → Estado → Guías → [12 opcionales visibles]
```

**Problemas:**
1. `user_id` visible por defecto — el comprador es un dato interno que no pertenece a la lectura principal
2. `OdooBot` como comprador en OCs automáticas contamina la percepción de ownership
3. 17 columnas visibles por defecto saturan cualquier pantalla
4. 7 columnas del bloque "opcional" están visibles por defecto contradiciendo el diseño intencionado
5. `reception_count` entre `state` y las opcionales rompe el cierre natural estado→fin

## 4.2 Jerarquía propuesta (corregida)

```
Proveedor → Ref Prov → OC → Contratado m³ → Recibido m³ → Pendiente m³ → Total USD → Recibido USD → Estado
                                                                              [9 columnas visibles]
+ opcionales ocultas por defecto: Facturación, Guías, % Completo, Fechas, Desvío, Lotes, Comprador
```

## 4.3 Veredicto sobre densidad

**17 columnas visibles = inaceptable para consola ejecutiva.**
**9 columnas visibles = profesional, completo, accionable.**

---

# 5. DECISIÓN DE DISEÑO FINAL

## 5.1 Principios rectores

1. **Proveedor primero.** `partner_id` antes que `name`. La consola cuenta desde el proveedor hacia adentro.
2. **user_id oculto por defecto.** El comprador es relevante para auditoría interna, no para la operación diaria. `OdooBot` no debe verse en la consola principal.
3. **Volumen tríptico.** Contratado → Recibido → Pendiente. Tres columnas contiguas sin interrupción.
4. **Dinero dúo.** Total contratado + Monto recibido. Dos columnas contiguas después del volumen.
5. **Cierre con estado.** Estado cierra la fila. Es el veredicto final de cada OC.
6. **9 columnas visibles máximo.**
7. **Opcionales reales.** Campos marcados `optional="show"` (ocultos por defecto) que el usuario puede activar si los necesita.
8. **Kanban neutralizado.** Reemplazar referencia a kanban estándar por uno propio sin dashboard KPI.

## 5.2 Lo que se mantiene

- Search view `view_purchase_order_madenat_search`: diseño sólido, orientado al negocio
- Tree view standalone sin herencia
- Decoraciones de color y estado
- `sample="1"`
- Orden descendente por fecha
- Contexto `search_default_state_purchase: 1`

## 5.3 Lo que se corrige

- 17 → 9 columnas visibles por defecto
- Orden de columnas reestructurado
- `optional="hide"` → `optional="show"` en columnas opcionales reales
- `partner_id` movido antes de `name`
- `partner_ref` movido a posición 2 (visible, entre proveedor y OC)
- `date_order` visible por defecto como 5ª columna (después del tríptico de volumen, antes del dinero)
- Kanban reemplazado por vista sin KPI retail

## 5.4 Lo que se elimina

- Referencia a `purchase.view_purchase_order_kanban` en view_ids
- Vista kanban estándar con KPI dashboard
- `user_id` de las columnas visibles

---

# 6. COLUMNAS FINALES

## 6.1 Orden definitivo y visibilidad

| # | Campo | String | Widget | Visibilidad | Justificación |
|---|---|---|---|---|---|
| 1 | `partner_id` | Proveedor | many2one_avatar | **visible** | Principal stakeholder externo. Jerarquía: proveedor primero. |
| 2 | `partner_ref` | Ref. Proveedor | — | **visible** | Referencia externa del proveedor. Clave para matching y comunicación. |
| 3 | `name` | OC | decoration-bf | **visible** | Identificador interno. Bold para jerarquía visual. |
| 4 | `lumber_volume_m3` | Contratado (m³) | digits | **visible** | Compromiso de volumen. Punto de partida de toda métrica. |
| 5 | `received_volume_m3` | Recibido (m³) | digits | **visible** | Lo que ya ingresó. Trazabilidad operativa. |
| 6 | `pending_volume_m3` | Pendiente (m³) | digits, decoration-danger | **visible** | Lo que falta. Accionable: si > 0, está en rojo. |
| 7 | `amount_total` | Total Contratado | monetary, decoration-bf, sum | **visible** | Compromiso financiero total. Sumable para totales. |
| 8 | `monto_recibido_usd` | Recibido (USD) | monetary | **visible** | Lo financieramente ejecutado. Par con amount_total. |
| 9 | `state` | Estado | badge, decorations | **visible** | Cierre de fila. Veredicto de la OC. |
| 10 | `invoice_status` | Facturación | badge | optional="show" | Relevante para finanzas, no para operación diaria. |
| 11 | `reception_count` | Guías | — | optional="show" | Conteo de guías. El volumen ya cuenta la historia principal. |
| 12 | `percent_completed` | % Completo | progressbar | optional="show" | Visualmente atractivo pero redundante con recibido/pendiente. |
| 13 | `date_order` | Fecha OC | — | optional="show" | La consola ya ordena por fecha descendente. |
| 14 | `date_approve` | Fecha Confirmación | — | optional="show" | Relevante para auditoría de ciclo de compra. |
| 15 | `variance_commercial_physical` | Desvío Vol. (%) | digits, decorations | optional="show" | Crítico para control de calidad pero no para lectura diaria. |
| 16 | `total_lots_count` | Lotes | — | optional="show" | Detalle fino de recepción. |
| 17 | `user_id` | Comprador | — | optional="show" | Dato interno. Oculto por defecto. `OdooBot` no contamina. |
| — | `provisional` | — | invisible="1" | invisible | Campo técnico para decoraciones y botón. |

**Total visible por defecto: 9 columnas.**
**Total disponible vía personalizar: 17 columnas.**

---

# 7. SEARCH VIEW FINAL

La search view actual (`view_purchase_order_madenat_search`) es **sólida y no requiere cambios estructurales**. Solo se recomienda un ajuste menor:

## 7.1 Lo que se mantiene igual

- Búsqueda unificada: `name`, `partner_ref`, `origin` → excelente
- Campo de búsqueda por proveedor con `child_of` → correcto
- Filtros de estado: draft, sent, purchase, done, cancel → completos
- Filtros operativos: pending_reception, no_reception, provisional_filter → excelentes para madera
- Filtro de desvío: variance_high > 5% → correcto
- Filtro de facturación: not_invoiced → correcto
- Agrupaciones: state, partner_id, user_id → cubren los 3 ejes relevantes

## 7.2 Cambio recomendado

- `user_id` en la search view se mantiene como filtro disponible (el usuario puede buscar por comprador si lo necesita), pero el campo `user_id` en la tree view queda en `optional="show"` (oculto por defecto). La search view no necesita que `user_id` esté visible en la tree para funcionar.

**Veredicto sobre KPI superiores en search view:**
- "valor promedio de la orden" → NO APARECE en esta search view. Correcto.
- "últimos 7 días" → NO APARECE. Correcto.
- "actividad" → NO APARECE. Correcto.
- "plazo de compra" → NO APARECE. Correcto.
- "RFQ enviadas" → NO APARECE. Correcto.
- **La search view está limpia de KPI retail.**

---

# 8. KPI / DASHBOARD

## 8.1 Estado actual

| Elemento | ¿Tiene KPI retail? | Origen |
|---|---|---|
| Tree view (list) | **NO** | `view_purchase_order_kpis_tree_madenat_pro` es `<list>` puro |
| Search view | **NO** | `view_purchase_order_madenat_search` no tiene tiles KPI |
| Kanban | **SÍ** | `purchase.view_purchase_order_kanban` llama `retrieve_dashboard` |
| Pivot | **SÍ** (potencial) | Sin view_id explícito, hereda pivot estándar |
| Graph | **SÍ** (potencial) | Sin view_id explícito, hereda graph estándar |

## 8.2 Decisión

1. **Kanban:** Reemplazar `purchase.view_purchase_order_kanban` por `False` en view_ids. Esto hará que Odoo genere una vista kanban por defecto sin KPI dashboard. Alternativa: crear un kanban mínimo sin `retrieve_dashboard`.
2. **Pivot y graph:** Mantener `False` (vistas generadas por defecto). No son la interfaz principal de esta consola. Si en el futuro se necesitan pivots específicos de madera, se crearán con view_id explícito.
3. **Tree view:** Sin cambios en cuanto a KPI. Ya está limpia.
4. **Search view:** Sin cambios. Ya está limpia.

**Conclusión tajante:**
- Los KPI genéricos de retail ("valor promedio", "últimos 7 días", "actividad", "RFQ enviadas") **deben eliminarse totalmente** de esta consola.
- El único punto donde persisten es el kanban estándar, que se elimina de los view_ids.
- La search view actual con filtros accionables (pendiente, sin recepción, desvío > 5%, por facturar) **reemplaza perfectamente** cualquier necesidad de KPI superior.

---

# 9. XML FINAL RECOMENDADO

Ver archivo: `custom_addons/madenat_lumber_purchasing/views/purchase_order_views_ce.xml`

---

# 10. VEREDICTO EJECUTIVO

## Diagnóstico raíz

La consola `action_madenat_purchase_order` tiene un **80% del trabajo bien hecho**:
- Tree view standalone sin herencia ✓
- Search view orientada al negocio maderero ✓
- Acción con view_ids explícitos ✓
- Contexto correcto (confirmadas primero) ✓
- Modelo de datos forestal completo ✓

El **20% restante son 4 problemas concretos**:

1. **17 columnas visibles por defecto** — El desarrollador usó `optional="hide"` en todo en vez de `optional="show"` en las opcionales. Corrección: 1 atributo por campo.
2. **Orden de columnas invertido** — `name` antes que `partner_id`. Corrección: mover `partner_id` a posición 1.
3. **Kanban hereda KPI retail** — `view_ids` referencia `purchase.view_purchase_order_kanban`. Corrección: cambiar a `False`.
4. **user_id visible por defecto** — El comprador es ruido para 3 de 4 perfiles. `OdooBot` contamina. Corrección: `optional="show"`.

## Gravedad

- **Crítico:** Columna 1 (17 visibles) — hace la consola inusable en pantallas normales
- **Alto:** Columna 3 (kanban KPI) — contamina la experiencia al cambiar de vista
- **Medio:** Columna 2 (orden partner_id) — no bloquea pero degrada la lectura
- **Bajo:** Columna 4 (user_id) — ruido manejable pero evitable

## Acción requerida

Reemplazar el contenido de `purchase_order_views_ce.xml` con el XML corregido. Es un cambio de ~40 líneas. Sin migraciones. Sin dependencias nuevas. Sin riesgo de regresión.

## Estado final esperado

- 9 columnas visibles, jerarquía Proveedor → Ref → OC → Volumen → Dinero → Estado
- 8 columnas opcionales ocultas por defecto
- Sin KPI retail en ninguna vista de la acción
- Search view intacta (ya es correcta)
- Consola profesional, sobria, ejecutiva, accionable