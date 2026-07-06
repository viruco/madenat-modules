# INFORME DE AUDITORÍA TÉCNICA: ACTION-521 vs ACTION-567
## Comparación de Acciones, Search Views y Consistencia Funcional

**Fecha:** 2026-06-19
**Auditor:** Equipo Técnico MADENAT
**Módulo:** `madenat_lumber_core`
**Versión:** 18.0.5.3.0

---

## RESUMEN EJECUTIVO

Se detectaron **4 hallazgos críticos**, **3 altos**, **3 medios** y **2 bajos** en la comparación entre las acciones de los modelos `madenat.guia.processing` (action-521) y `lumber.reception` (action-567). El problema más grave es una **colisión real de XML ID** para `action_madenat_guia_processing` definida en dos archivos distintos del mismo módulo, donde la definición que prevalece es la más incompleta. Adicionalmente, existe otra colisión en `view_madenat_guia_processing_list` que hace que se cargue una vista lista empobrecida en lugar de la versión rica con decoraciones. La search view de `madenat.guia.processing` carece de filtro para el estado `verified`, carece de group by por `order_id`, y el contexto inicial de `action_guia_processing_list` fuerza restrictivamente el filtro `draft`.

---

## HALLAZGOS CRÍTICOS

### H-C1: Colisión de XML ID `action_madenat_guia_processing` — Definición Duplicada en Dos Archivos

- **Descripción:** El XML ID `action_madenat_guia_processing` está definido en dos archivos distintos dentro del mismo módulo `madenat_lumber_core`.
- **Causa raíz:** El archivo `guia_processing_list_search.xml` se creó como una extensión/refactor sin eliminar la definición original en `guia_processing_views.xml`. Ambos archivos se cargan en el manifest (líneas 33 y 34).
- **Evidencia concreta:**
  - Archivo 1: `custom_addons/madenat_lumber_core/views/guia_processing_views.xml` — línea 1061
  - Archivo 2: `custom_addons/madenat_lumber_core/views/guia_processing_list_search.xml` — línea 72
  - Orden de carga en `__manifest__.py` línea 33-34: `guia_processing_views.xml` → `guia_processing_list_search.xml`
- **Impacto funcional:** La segunda definición (guia_processing_list_search.xml) sobrescribe completamente a la primera. Esto causa:
  - La acción cargada NO tiene `view_id` explícito → Odoo selecciona la vista list por defecto.
  - La acción cargada SÍ tiene `search_view_id` → apunta correctamente a `view_madenat_guia_processing_search`.
  - La acción cargada NO tiene `domain` → las guías canceladas aparecen en la lista.
  - La acción cargada NO tiene `context` → sin filtros por defecto.
  - La acción original de `guia_processing_views.xml` (línea 1061) también carecía de `domain`, `context`, `view_id` y `search_view_id`, por lo que la versión que prevalece (con search_view_id) es marginalmente mejor, pero ambas son incompletas.
- **Recomendación exacta:** Eliminar la definición duplicada en `guia_processing_views.xml` (líneas 1054-1074) y consolidar TODOS los campos necesarios en la definición de `guia_processing_list_search.xml`.
- **Riesgo de aplicar mal la corrección:** Si se elimina la definición equivocada, se pierde el `search_view_id`. La acción correcta a conservar es la de `guia_processing_list_search.xml` porque tiene `search_view_id`. Pero hay que añadirle `domain`, `context` y `view_id`.

### H-C2: Colisión de XML ID `view_madenat_guia_processing_list` — Vista List Duplicada y Empobrecida

- **Descripción:** El XML ID `view_madenat_guia_processing_list` está definido en dos archivos con contenido diferente. La versión que prevalece es la más simple y menos informativa.
- **Causa raíz:** Misma causa que H-C1: `guia_processing_list_search.xml` redefinió la vista lista sin eliminar la original.
- **Evidencia concreta:**
  - Archivo 1: `custom_addons/madenat_lumber_core/views/guia_processing_views.xml` — línea 29
    - Versión RICA: 12 campos visibles (name, tipo_recepcion, date_emission, partner_id, order_id, oc_reference_raw, vol_comercial, vol_fisico, diff_pct, total_paquetes, state), decoraciones por estado (decoration-muted, success, danger), widget percentage, widget badge.
  - Archivo 2: `custom_addons/madenat_lumber_core/views/guia_processing_list_search.xml` — línea 7
    - Versión POBRE: 7 campos visibles (name, date_emission, partner_id, order_id, vol_comercial, vol_fisico, total_paquetes, additional_cost, state), sin campo `tipo_recepcion` ni `diff_pct`, con menos decoraciones.
- **La definición efectiva:** La de `guia_processing_list_search.xml` (línea 7) porque se carga después.
- **Impacto funcional:** Los usuarios de `action_guia_processing_list` (menú "Guías Procesadas") ven la versión pobre, perdiendo:
  - Columna `tipo_recepcion` (crítica para diferenciar tipos de guía)
  - Columna `diff_pct` con widget percentage (KPI de desviación de volúmenes)
  - Columna `oc_reference_raw`
  - Decoraciones visuales más ricas
- **Recomendación exacta:** Eliminar la definición de `view_madenat_guia_processing_list` en `guia_processing_list_search.xml` (líneas 7-34 completas). La vista correcta es la de `guia_processing_views.xml` (líneas 29-68).
- **Riesgo de aplicar mal la corrección:** Ninguno si se elimina solo el bloque del record `view_madenat_guia_processing_list` en `guia_processing_list_search.xml`. La vista rica en `guia_processing_views.xml` es autosuficiente.

### H-C3: Search View sin Filtro para Estado `verified`

- **Descripción:** La search view `view_madenat_guia_processing_search` carece de filtro para el estado `verified`, que es un estado intermedio crítico en el flujo de negocio (draft → verified → validated).
- **Causa raíz:** La search view se diseñó cuando el modelo posiblemente solo tenía 3 estados, o se omitió por descuido al agregar el estado `verified`.
- **Evidencia concreta:**
  - Archivo: `custom_addons/madenat_lumber_core/views/guia_processing_list_search.xml` — líneas 56-58
  - Filtros existentes: `filter_draft` (draft), `filter_validated` (validated), `filter_cancelled` (cancelled)
  - Filtro faltante: `filter_verified` para estado `verified`
  - El modelo en `madenat_guia_processing.py` confirma que `verified` es un estado válido del flujo.
- **Impacto funcional:** Los operadores no pueden filtrar rápidamente guías en estado "verified" (datos cargados y verificados, listas para validación). Deben usar búsqueda manual por el campo `state`, lo cual es ineficiente y propenso a error.
- **Recomendación exacta:** Agregar un filtro `filter_verified` en `view_madenat_guia_processing_search` entre `filter_draft` y `filter_validated`.
- **Riesgo de aplicar mal la corrección:** Ninguno. Es una adición pura, no modifica filtros existentes.

### H-C4: Contexto Inicial Excesivamente Restrictivo en `action_guia_processing_list`

- **Descripción:** La acción `action_guia_processing_list` fuerza el filtro `search_default_filter_draft: 1`, lo que hace que al entrar al menú "Guías Procesadas" el usuario solo vea guías en estado borrador.
- **Causa raíz:** Probablemente se configuró así durante desarrollo/pruebas y nunca se ajustó para producción.
- **Evidencia concreta:**
  - Archivo: `custom_addons/madenat_lumber_core/views/lumber_core_menu.xml` — línea 47
  - Contexto: `{'search_default_filter_draft': 1, 'default_tipo_recepcion': 'service'}`
- **Impacto funcional:**
  - El usuario NO ve guías en estados `verified` o `validated` al ingresar, a menos que manualmente desactive el filtro.
  - El nombre del menú es "Guías Procesadas (Servicios)", lo cual sugiere que deberían verse guías ya procesadas, no solo borradores.
  - Esto genera confusión operativa: el operador podría pensar que no hay guías cuando en realidad el filtro las oculta.
- **Recomendación exacta:** Cambiar el contexto a `{'search_default_group_by_state': 1}` o simplemente `{}` para mostrar todas las guías sin filtro restrictivo. Si se quiere un filtro por defecto útil, usar `search_default_filter_verified` (una vez creado, ver H-C3).
- **Riesgo de aplicar mal la corrección:** Si se elimina completamente el contexto, se pierde el `default_tipo_recepcion: 'service'` que puede ser necesario para la creación de nuevos registros. Evaluar si realmente se necesita.

---

## HALLAZGOS ALTOS

### H-A1: Domain no Excluye Canceladas en Acciones de `madenat.guia.processing`

- **Descripción:** Ninguna de las acciones del modelo `madenat.guia.processing` excluye registros en estado `cancelled` del domain base, a diferencia de `action_lumber_reception_pending` (action-567) que sí lo hace con `[('state', 'not in', ['cancelled'])]`.
- **Causa raíz:** Omisión en el diseño de las acciones de `madenat.guia.processing`.
- **Evidencia concreta:**
  - `action_madenat_guia_processing` en `guia_processing_list_search.xml` línea 72: sin domain → incluye canceladas.
  - `action_guia_processing_list` en `lumber_core_menu.xml` línea 46: domain `[('tipo_recepcion', '!=', 'raw')]` → NO excluye canceladas.
  - `action_lumber_reception_pending` en `lumber_core_menu.xml` línea 20: domain `[('state', 'not in', ['cancelled'])]` → SÍ excluye canceladas.
- **Impacto funcional:** Las guías canceladas aparecen mezcladas en la lista principal, obligando al usuario a filtrarlas manualmente. Esto degrada la UX y aumenta el riesgo de error operativo (por ejemplo, intentar operar sobre una guía cancelada).
- **Recomendación exacta:** Agregar `[('state', 'not in', ['cancelled'])]` al domain de `action_guia_processing_list` (o combinar con el domain existente: `[('tipo_recepcion', '!=', 'raw'), ('state', 'not in', ['cancelled'])]`).
- **Riesgo de aplicar mal la corrección:** Si se reemplaza el domain existente en lugar de extenderlo, se pierde la exclusión de `tipo_recepcion == 'raw'`.

### H-A2: Search View sin Group By por `order_id`

- **Descripción:** La search view `view_madenat_guia_processing_search` carece de agrupación por `order_id` (Orden de Compra), mientras que `view_lumber_reception_search` (action-567) sí tiene `group_by_purchase_order`.
- **Causa raíz:** La search view de `madenat.guia.processing` es anterior o no se actualizó cuando se añadió el campo `order_id`.
- **Evidencia concreta:**
  - `view_madenat_guia_processing_search` en `guia_processing_list_search.xml` líneas 60-63: agrupaciones existentes: `group_partner`, `group_state`, `group_date`. Falta `group_order`.
  - `view_lumber_reception_search` en `lumber_reception_views.xml` líneas 547-549: tiene `group_by_purchase_order`.
  - La vista lista de `madenat.guia.processing` (guia_processing_views.xml línea 45) SÍ muestra el campo `order_id`, confirmando que el campo existe y es relevante.
- **Impacto funcional:** Los operadores no pueden agrupar guías por OC para revisar todas las guías asociadas a una misma orden de compra. Esto es especialmente útil cuando una OC genera múltiples guías parciales.
- **Recomendación exacta:** Agregar filtro de agrupación `group_order` con `context="{'group_by': 'order_id'}"` en `view_madenat_guia_processing_search`.
- **Riesgo de aplicar mal la corrección:** Ninguno. Es una adición pura.

### H-A3: Vista List Efectiva es Inferior a la Vista List Declarada en Form View

- **Descripción:** La vista form (`view_madenat_guia_processing_form`) hace referencia a campos y estructuras que no están presentes en la vista list que efectivamente se carga (debido a la colisión H-C2).
- **Causa raíz:** La colisión H-C2 provoca que la vista list cargada sea una versión antigua/simplificada que no está alineada con la vista form completa.
- **Evidencia concreta:**
  - Vista list efectiva (`guia_processing_list_search.xml` línea 7-33): no tiene `tipo_recepcion` ni `diff_pct`.
  - Vista form (`guia_processing_views.xml` línea 87-1021): tiene `tipo_recepcion` como campo requerido y `diff_pct` como indicador KPI central con dashboard visual.
- **Impacto funcional:** Desalineación entre la experiencia de lista y formulario. El usuario no puede identificar rápidamente el tipo de recepción ni la desviación de volumen desde la lista.
- **Recomendación exacta:** Aplicar la corrección de H-C2 (eliminar la vista duplicada). Esto restaurará la vista lista rica que incluye `tipo_recepcion` y `diff_pct`.
- **Riesgo de aplicar mal la corrección:** Cubierto por H-C2.

---

## HALLAZGOS MEDIOS

### H-M1: Action-521 Carece de `view_id` Explícito en Definición Efectiva

- **Descripción:** La definición efectiva de `action_madenat_guia_processing` (guia_processing_list_search.xml línea 72) no especifica `view_id`, dejando que Odoo seleccione la vista por defecto mediante resolución interna.
- **Causa raíz:** La definición se creó sin `view_id`, posiblemente asumiendo que Odoo elegiría correctamente.
- **Evidencia concreta:**
  - `guia_processing_list_search.xml` línea 72-85: sin campo `view_id`.
  - `action_lumber_reception_pending` (lumber_core_menu.xml línea 18): tiene `view_id` explícito.
- **Impacto funcional:** En entornos con múltiples vistas list para el mismo modelo, Odoo podría seleccionar una vista no deseada. Actualmente el comportamiento es predecible porque solo hay una vista list cargada (la pobre), pero tras corregir H-C2 conviene hacer explícita la referencia.
- **Recomendación exacta:** Agregar `<field name="view_id" ref="view_madenat_guia_processing_list"/>` a la definición en `guia_processing_list_search.xml`.
- **Riesgo de aplicar mal la corrección:** Ninguno si se usa la referencia correcta.

### H-M2: Filtro `filter_cancelled` en Search View es Contradictorio con Mejor Práctica

- **Descripción:** La search view de `madenat.guia.processing` incluye un filtro para `cancelled`, lo cual es útil para auditoría, pero la acción base no excluye canceladas del domain. Esto es inconsistente con action-567.
- **Causa raíz:** Diseño no unificado entre las acciones de los dos modelos.
- **Evidencia concreta:**
  - `guia_processing_list_search.xml` línea 58: filtro `filter_cancelled`.
  - `lumber_core_menu.xml` línea 20: action-567 excluye canceladas del domain base.
- **Impacto funcional:** Inconsistencia en la experiencia de usuario entre los dos modelos. En `lumber.reception`, las canceladas están ocultas por defecto; en `madenat.guia.processing`, no.
- **Recomendación exacta:** Unificar criterio: el domain base debe excluir canceladas (H-A1), pero mantener el filtro `filter_cancelled` en la search view para que el usuario pueda verlas explícitamente si lo desea.
- **Riesgo de aplicar mal la corrección:** Cubierto por H-A1.

### H-M3: Ausencia de Filtros por `tipo_recepcion` en Search View

- **Descripción:** La search view `view_madenat_guia_processing_search` no tiene filtros para `tipo_recepcion`, un campo clave que diferencia tipos de guía (service, raw, etc.).
- **Causa raíz:** La search view no se actualizó cuando se añadió el campo `tipo_recepcion`.
- **Evidencia concreta:**
  - `guia_processing_list_search.xml` líneas 49-54: campos de búsqueda disponibles: name, date_emission, partner_id, order_id, state. Falta `tipo_recepcion`.
  - `lumber_core_menu.xml` línea 46: domain usa `tipo_recepcion`, lo que confirma su importancia.
- **Impacto funcional:** El usuario no puede filtrar por tipo de recepción desde la search view, a pesar de que el domain de la acción ya filtra por este campo. Si se quiere ver todos los tipos, hay que quitar el domain, pero luego no hay forma de filtrar en la UI.
- **Recomendación exacta:** Agregar `<field name="tipo_recepcion" string="Tipo de Recepción"/>` a la search view y un filtro rápido `<filter name="filter_service" string="Servicio" domain="[('tipo_recepcion','=','service')]"/>`.
- **Riesgo de aplicar mal la corrección:** Ninguno.

---

## HALLAZGOS BAJOS

### H-B1: Action-521 no Define `multi_edit` ni `sample` en la Vista List

- **Descripción:** La vista list efectiva de `madenat.guia.processing` no habilita `multi_edit="1"` ni `sample="1"`, a diferencia de `view_lumber_reception_list` que sí los tiene.
- **Causa raíz:** La vista duplicada (guia_processing_list_search.xml) no incluye estos atributos, a diferencia de la versión moderna en lumber_reception.
- **Evidencia concreta:**
  - `guia_processing_list_search.xml` línea 11: `<list string="Guías Procesadas" ...>` sin multi_edit ni sample.
  - `lumber_reception_views.xml` línea 13-16: `<list ... multi_edit="1" sample="1" ...>`
- **Impacto funcional:** Los usuarios no pueden editar múltiples registros simultáneamente desde la vista lista ni ver datos de muestra. Esto es una deficiencia de UX menor.
- **Recomendación exacta:** Al corregir H-C2, la vista rica de `guia_processing_views.xml` (que tampoco tiene multi_edit/sample) será la que se cargue. Se recomienda agregar `multi_edit="1"` y `sample="1"` a esa vista.
- **Riesgo de aplicar mal la corrección:** `multi_edit` puede ser peligroso si hay campos computed que no se actualizan correctamente en edición masiva. Verificar antes de habilitar.

### H-B2: `search_default_order_by_date` en Action-567 sin Filtro Equivalente en Action-521

- **Descripción:** `action_lumber_reception_pending` aplica `search_default_order_by_date: 1` en su contexto, ordenando por fecha descendente. Las acciones de `madenat.guia.processing` no tienen orden por defecto.
- **Causa raíz:** Diferencia de diseño entre las dos acciones.
- **Evidencia concreta:**
  - `lumber_core_menu.xml` línea 21: `'search_default_order_by_date': 1`
  - `guia_processing_list_search.xml` líneas 72-85: sin contexto ni orden.
- **Impacto funcional:** Las guías en `madenat.guia.processing` se muestran en orden de creación (ID) por defecto en lugar de por fecha, lo cual es menos intuitivo.
- **Recomendación exacta:** Agregar `search_default_order_by_date` al contexto de `action_guia_processing_list`. Requiere que el filtro `order_by_date` exista en la search view (actualmente no existe en `view_madenat_guia_processing_search`).
- **Riesgo de aplicar mal la corrección:** Primero hay que crear el filtro `order_by_date` en la search view de `madenat.guia.processing`.

---

## TABLA COMPARATIVA ACTION-521 vs ACTION-567

| Dimensión | action-521 (`action_guia_processing_list`) | action-567 (`action_lumber_reception_pending`) | ¿Iguales? |
|---|---|---|---|
| **Modelo** | `madenat.guia.processing` | `lumber.reception` | ❌ Distinto (esperado) |
| **Nombre** | Guías Procesadas (Servicios) | Consola de Recepciones | ❌ Distinto (esperado) |
| **view_mode** | `list,form` | `list,form` | ✅ Igual |
| **view_id** | `view_madenat_guia_processing_list` | `madenat_lumber_core.view_lumber_reception_list` | ✅ Ambos especifican |
| **search_view_id** | `view_madenat_guia_processing_search` | `madenat_lumber_core.view_lumber_reception_search` | ✅ Ambos especifican |
| **domain** | `[('tipo_recepcion', '!=', 'raw')]` | `[('state', 'not in', ['cancelled'])]` | ❌ 521 no excluye canceladas |
| **context** | `{'search_default_filter_draft': 1, 'default_tipo_recepcion': 'service'}` | `{'search_default_group_by_purchase_order': 1, 'search_default_order_by_date': 1}` | ❌ 521 restrictivo (solo draft) |
| **Filtros search: draft** | ✅ `filter_draft` | ✅ `state_draft` | ✅ |
| **Filtros search: verified** | ❌ NO EXISTE | ✅ `state_verified` | ❌ CRÍTICO |
| **Filtros search: done/validated** | ✅ `filter_validated` | ✅ `state_done` | ✅ |
| **Filtros search: cancelled** | ✅ `filter_cancelled` | ❌ (excluido del domain) | ❌ Difiere estrategia |
| **Filtros search: tolerancia** | ❌ No aplica (no tiene campo) | ✅ 4 filtros (ok, warning, critical, needs_attention) | ❌ (modelo distinto) |
| **Group by: order_id/OC** | ❌ NO EXISTE | ✅ `group_by_purchase_order` | ❌ FALTANTE |
| **Group by: state** | ✅ `group_state` | ✅ `group_by_state` | ✅ |
| **Group by: supplier** | ✅ `group_partner` | ✅ `group_by_supplier` | ✅ |
| **Group by: date** | ✅ `group_date` | ✅ `group_by_date_month` | ✅ |
| **Group by: tolerance** | ❌ No aplica | ✅ `group_by_tolerance` | ❌ (modelo distinto) |
| **Group by: tipo_recepcion** | ❌ NO EXISTE | ❌ No aplica (no tiene campo) | ❌ FALTANTE |
| **default_order** | ❌ No definido | ✅ `reception_date desc` (vía contexto) | ❌ |
| **multi_edit** | ❌ No habilitado | ✅ `1` | ❌ |
| **sample** | ❌ No habilitado | ✅ `1` | ❌ |
| **Excluye canceladas del domain** | ❌ NO | ✅ SÍ | ❌ |

---

## PLAN DE REMEDIACIÓN PRIORIZADO

### FASE 1: Correcciones Críticas (ventana de mantenimiento inmediata)

| # | Acción | Archivo | Tipo |
|---|---|---|---|
| 1 | Eliminar `view_madenat_guia_processing_list` duplicado | `guia_processing_list_search.xml` L7-34 | Eliminación |
| 2 | Eliminar `action_madenat_guia_processing` duplicado | `guia_processing_views.xml` L1054-1074 | Eliminación |
| 3 | Agregar `view_id` explícito a `action_madenat_guia_processing` | `guia_processing_list_search.xml` L72-85 | Adición |
| 4 | Agregar filtro `filter_verified` a search view | `guia_processing_list_search.xml` L56-58 | Adición |

### FASE 2: Correcciones Altas (siguiente ventana)

| # | Acción | Archivo | Tipo |
|---|---|---|---|
| 5 | Agregar `domain` con exclusión de canceladas a `action_guia_processing_list` | `lumber_core_menu.xml` L46 | Modificación |
| 6 | Agregar group by `order_id` a search view | `guia_processing_list_search.xml` L60-63 | Adición |
| 7 | Corregir contexto restrictivo de `action_guia_processing_list` | `lumber_core_menu.xml` L47 | Modificación |
| 8 | Agregar `domain` con exclusión de canceladas a `action_madenat_guia_processing` | `guia_processing_list_search.xml` L72-85 | Adición |

### FASE 3: Correcciones Medias y Bajas (siguiente ciclo)

| # | Acción | Archivo | Tipo |
|---|---|---|---|
| 9 | Agregar campo `tipo_recepcion` a search view | `guia_processing_list_search.xml` L49-54 | Adición |
| 10 | Agregar filtro `order_by_date` a search view y contexto | `guia_processing_list_search.xml` | Adición |
| 11 | Agregar `multi_edit` y `sample` a vista list | `guia_processing_views.xml` L33 | Modificación |

---

## DIFF PROPUESTO EXACTO POR ARCHIVO

### Archivo 1: `custom_addons/madenat_lumber_core/views/guia_processing_views.xml`

#### Cambio 1.1: Eliminar definición duplicada de `action_madenat_guia_processing`

```diff
------- SEARCH
    <!--
    ═══════════════════════════════════════════════════════════════════════════════
    ACCIONES DE VENTANA
    ═══════════════════════════════════════════════════════════════════════════════
    -->

    <!-- Acción Principal: Todas las Guías -->
 <record id="action_madenat_guia_processing" model="ir.actions.act_window">
        <field name="name">Recepción de Guías</field>
        <field name="res_model">madenat.guia.processing</field>
        <field name="view_mode">list,form</field>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                Cargue su primera guía de despacho
            </p>
            <p>
                Siga la REGLA DE ORO: Ingrese los datos físicos para calcular volúmenes métricos (1M)
                y de exportación (1550/5085) con el ajuste de 1/8".
            </p>
        </field>
    </record>

   <record id="action_madenat_guia_processing_pending" model="ir.actions.act_window">
=======
    <!-- Las acciones de ventana para madenat.guia.processing están definidas
         en guia_processing_list_search.xml (action_madenat_guia_processing)
         y en lumber_core_menu.xml (action_guia_processing_list).
         Esta sección se elimina para resolver colisión de XML ID. -->
   <record id="action_madenat_guia_processing_pending" model="ir.actions.act_window">
+++++++ REPLACE
```

#### Cambio 1.2: Agregar `multi_edit` y `sample` a la vista list

```diff
------- SEARCH
            <list string="Recepción de Guías"
                  decoration-muted="state == 'draft'"
                  decoration-success="state == 'validated'"
                  decoration-danger="state == 'cancelled'">
=======
            <list string="Recepción de Guías"
                  multi_edit="1"
                  sample="1"
                  default_order="date_emission desc, name desc"
                  decoration-muted="state == 'draft'"
                  decoration-success="state == 'validated'"
                  decoration-danger="state == 'cancelled'">
+++++++ REPLACE
```

### Archivo 2: `custom_addons/madenat_lumber_core/views/guia_processing_list_search.xml`

#### Cambio 2.1: Eliminar definición duplicada de `view_madenat_guia_processing_list`

```diff
------- SEARCH
    <!-- ================================================== -->
    <!-- VISTA DE LISTA (Actualizado a <list> en Odoo 18) -->
    <!-- ================================================== -->
    <record id="view_madenat_guia_processing_list" model="ir.ui.view">
        <field name="name">madenat.guia.processing.list</field>
        <field name="model">madenat.guia.processing</field>
        <field name="arch" type="xml">
            <list string="Guías Procesadas" 
                  decoration-muted="state == 'draft'"
                  decoration-success="state == 'validated'"
                  decoration-danger="state == 'cancelled'">
                
                <field name="name" string="Número de Guía" />
                <field name="date_emission" string="Fecha de Emisión" />
                <field name="partner_id" string="Proveedor / Transportista" />
                <field name="order_id" string="Orden de Compra" />
                
                <field name="vol_comercial" string="Vol. Comercial" optional="show"/>
                <field name="vol_fisico" string="Vol. Físico" optional="show"/>
                <field name="total_paquetes" string="Paquetes" optional="hide"/>
                
                <field name="additional_cost" string="Costo Adicional" widget="monetary" optional="hide"/>
                
                <field name="state" string="Estado" widget="badge"
                       decoration-success="state == 'validated'"
                       decoration-info="state == 'processed'"
                       decoration-muted="state == 'draft'"
                       decoration-danger="state == 'cancelled'"/>
            </list>
        </field>
    </record>

    <!-- 
       🚨 IMPORTANTE: Se eliminó 'view_madenat_guia_processing_form' de este archivo.
       La versión correcta del formulario (con el chatter arreglado) 
       está en el archivo 'guia_processing_views.xml'.
    -->

    <!-- ================================================== -->
    <!-- VISTA DE BÚSQUEDA -->
    <!-- ================================================== -->
=======
    <!-- 
       🚨 IMPORTANTE: 'view_madenat_guia_processing_list' fue eliminado de este archivo
       por estar duplicado. La versión canónica está en guia_processing_views.xml.
       'view_madenat_guia_processing_form' también está en guia_processing_views.xml.
    -->

    <!-- ================================================== -->
    <!-- VISTA DE BÚSQUEDA -->
    <!-- ================================================== -->
+++++++ REPLACE
```

#### Cambio 2.2: Agregar filtro `filter_verified` a la search view

```diff
------- SEARCH
                <filter name="filter_draft" string="Borrador" domain="[('state','=','draft')]"/>
                <filter name="filter_validated" string="Validada" domain="[('state','=','validated')]"/>
                <filter name="filter_cancelled" string="Cancelada" domain="[('state','=','cancelled')]"/>
=======
                <filter name="filter_draft" string="Borrador" domain="[('state','=','draft')]"/>
                <filter name="filter_verified" string="Verificada" domain="[('state','=','verified')]"/>
                <filter name="filter_validated" string="Validada" domain="[('state','=','validated')]"/>
                <filter name="filter_cancelled" string="Cancelada" domain="[('state','=','cancelled')]"/>
+++++++ REPLACE
```

#### Cambio 2.3: Agregar group by `order_id` a la search view

```diff
------- SEARCH
                <group expand="0" string="Agrupar Por">
                    <filter string="Proveedor" name="group_partner" context="{'group_by': 'partner_id'}"/>
                    <filter string="Estado" name="group_state" context="{'group_by': 'state'}"/>
                    <filter string="Fecha" name="group_date" context="{'group_by': 'date_emission'}"/>
                </group>
=======
                <group expand="0" string="Agrupar Por">
                    <filter string="Proveedor" name="group_partner" context="{'group_by': 'partner_id'}"/>
                    <filter string="Orden de Compra" name="group_order" context="{'group_by': 'order_id'}"/>
                    <filter string="Estado" name="group_state" context="{'group_by': 'state'}"/>
                    <filter string="Fecha" name="group_date" context="{'group_by': 'date_emission'}"/>
                </group>
+++++++ REPLACE
```

#### Cambio 2.4: Agregar filtro `order_by_date` a la search view

```diff
------- SEARCH
            <search string="Buscar Guías">
                <field name="name" string="Número de Guía"/>
                <field name="date_emission" string="Fecha de Emisión"/>
                <field name="partner_id" string="Proveedor"/>
                <field name="order_id" string="Orden de Compra"/>
                <field name="state" string="Estado"/>
                
                <filter name="filter_draft" string="Borrador" domain="[('state','=','draft')]"/>
=======
            <search string="Buscar Guías">
                <field name="name" string="Número de Guía"/>
                <field name="date_emission" string="Fecha de Emisión"/>
                <field name="partner_id" string="Proveedor"/>
                <field name="order_id" string="Orden de Compra"/>
                <field name="state" string="Estado"/>
                
                <filter name="order_by_date" string="Más Recientes"
                        domain="[]"
                        context="{'order': 'date_emission desc'}"/>
                <separator/>
                
                <filter name="filter_draft" string="Borrador" domain="[('state','=','draft')]"/>
+++++++ REPLACE
```

#### Cambio 2.5: Agregar `view_id`, `domain` y `context` a la acción

```diff
------- SEARCH
    <record id="action_madenat_guia_processing" model="ir.actions.act_window">
        <field name="name">Recepción de Guías</field>
        <field name="res_model">madenat.guia.processing</field>
        <field name="view_mode">list,form</field>
        <field name="search_view_id" ref="view_madenat_guia_processing_search"/>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                Crea tu primera Recepción de Guía
            </p>
            <p>
                Gestiona la carga masiva de guías de despacho mediante PDF y Excel.
            </p>
        </field>
    </record>
=======
    <record id="action_madenat_guia_processing" model="ir.actions.act_window">
        <field name="name">Recepción de Guías</field>
        <field name="res_model">madenat.guia.processing</field>
        <field name="view_mode">list,form</field>
        <field name="view_id" ref="madenat_lumber_core.view_madenat_guia_processing_list"/>
        <field name="search_view_id" ref="view_madenat_guia_processing_search"/>
        <field name="domain">[('state', 'not in', ['cancelled'])]</field>
        <field name="context">{'search_default_order_by_date': 1}</field>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                Crea tu primera Recepción de Guía
            </p>
            <p>
                Gestiona la carga masiva de guías de despacho mediante PDF y Excel.
            </p>
        </field>
    </record>
+++++++ REPLACE
```

### Archivo 3: `custom_addons/madenat_lumber_core/views/lumber_core_menu.xml`

#### Cambio 3.1: Corregir domain y context de `action_guia_processing_list`

```diff
------- SEARCH
        <record id="action_guia_processing_list" model="ir.actions.act_window">
            <field name="name">Guías Procesadas (Servicios)</field>
            <field name="res_model">madenat.guia.processing</field>
            <field name="view_mode">list,form</field>
            <field name="view_id" ref="view_madenat_guia_processing_list"/>
            <field name="search_view_id" ref="view_madenat_guia_processing_search"/>
            <field name="domain">[('tipo_recepcion', '!=', 'raw')]</field>
            <field name="context">{'search_default_filter_draft': 1, 'default_tipo_recepcion': 'service'}</field>
        </record>
=======
        <record id="action_guia_processing_list" model="ir.actions.act_window">
            <field name="name">Guías Procesadas (Servicios)</field>
            <field name="res_model">madenat.guia.processing</field>
            <field name="view_mode">list,form</field>
            <field name="view_id" ref="view_madenat_guia_processing_list"/>
            <field name="search_view_id" ref="view_madenat_guia_processing_search"/>
            <field name="domain">[('tipo_recepcion', '!=', 'raw'), ('state', 'not in', ['cancelled'])]</field>
            <field name="context">{'search_default_order_by_date': 1, 'default_tipo_recepcion': 'service'}</field>
        </record>
+++++++ REPLACE
```

---

## PRUEBAS DE VALIDACIÓN POST-CAMBIO

### Prueba 1: Verificar que no hay colisión de XML IDs
```bash
# Buscar definiciones duplicadas del XML ID
grep -rn "id=\"action_madenat_guia_processing\"" custom_addons/madenat_lumber_core/views/
grep -rn "id=\"view_madenat_guia_processing_list\"" custom_addons/madenat_lumber_core/views/
# Resultado esperado: exactamente 1 ocurrencia de cada uno (no en RAW/legacy)
```

### Prueba 2: Verificar que la vista list cargada es la versión rica
```bash
# Actualizar módulo y verificar en UI:
# - Menú "Guías Procesadas" debe mostrar columnas: name, tipo_recepcion, date_emission, partner_id, order_id, oc_reference_raw, vol_comercial, vol_fisico, diff_pct, total_paquetes, state
# - Decoraciones: draft=muted, validated=success, cancelled=danger
# - Widget percentage en diff_pct
# - Widget badge en state
```

### Prueba 3: Verificar filtro `verified` en search view
```bash
# En UI:
# 1. Abrir menú "Guías Procesadas"
# 2. Verificar que en la search view aparecen los filtros: Borrador, Verificada, Validada, Cancelada
# 3. Seleccionar "Verificada" y confirmar que solo muestra registros con state='verified'
```

### Prueba 4: Verificar group by `order_id`
```bash
# En UI:
# 1. Abrir search view de "Guías Procesadas"
# 2. Desplegar "Agrupar Por"
# 3. Verificar que existe "Orden de Compra"
# 4. Seleccionarlo y confirmar que agrupa correctamente
```

### Prueba 5: Verificar exclusión de canceladas
```bash
# En UI:
# 1. Crear una guía y cancelarla
# 2. Ir al menú "Guías Procesadas"
# 3. Verificar que la guía cancelada NO aparece en la lista
# 4. Seleccionar filtro "Cancelada" en search view
# 5. Verificar que AHORA SÍ aparece
```

### Prueba 6: Verificar orden por defecto
```bash
# En UI:
# 1. Abrir "Guías Procesadas"
# 2. Verificar que los registros aparecen ordenados por fecha de emisión descendente
```

### Prueba 7: Verificar contexto no restrictivo
```bash
# En UI:
# 1. Abrir "Guías Procesadas"
# 2. Verificar que se muestran guías en todos los estados (draft, verified, validated)
# 3. Verificar que el filtro "Borrador" NO está activado por defecto
```

---

## RIESGOS Y DEPENDENCIAS

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Otro módulo hereda `view_madenat_guia_processing_list` de guia_processing_list_search.xml | Baja | Alto | Verificar con `grep -rn "inherit_id.*view_madenat_guia_processing_list" custom_addons/` antes de eliminar. El resultado muestra que `madenat_toll_processing` hereda de `view_madenat_guia_processing_form`, no de la vista list. |
| `action_madenat_guia_processing` es referenciada por código Python o datos | Media | Alto | Buscar con `grep -rn "action_madenat_guia_processing" custom_addons/ --include="*.py" --include="*.xml" --include="*.csv"` excluyendo RAW/legacy. |
| `multi_edit="1"` causa errores en edición masiva | Media | Medio | Probar en entorno de staging antes de producción. |
| Cambio de contexto rompe flujo de creación de registros | Baja | Medio | El `default_tipo_recepcion: 'service'` se conserva en `action_guia_processing_list` para no afectar la creación de nuevos registros. |
| El filtro `order_by_date` usa `date_emission` que podría ser NULL en algunos registros | Baja | Bajo | Los registros sin fecha aparecerán al final. Es comportamiento esperado de Odoo. |

---

## CONCLUSIÓN FINAL

La auditoría revela que el módulo `madenat_lumber_core` contiene **dos colisiones reales de XML ID** que provocan que la vista lista y la acción efectivamente cargadas para el modelo `madenat.guia.processing` sean versiones incompletas o empobrecidas respecto a las definiciones canónicas. Esto genera una experiencia de usuario degradada y una desalineación funcional significativa respecto al modelo `lumber.reception` (action-567), que sirve como referencia de buenas prácticas dentro del mismo ecosistema.

**Impacto operativo principal:**
1. Los usuarios de "Guías Procesadas" ven una vista lista con menos columnas y sin indicadores KPI (diff_pct, tipo_recepcion).
2. No pueden filtrar por estado `verified`, obligando a búsquedas manuales.
3. No pueden agrupar por `order_id`, dificultando la gestión de guías por OC.
4. Las guías canceladas aparecen mezcladas con las activas.
5. El contexto inicial fuerza el filtro `draft`, ocultando guías en otros estados.

**Severidad global: CRÍTICA** — requiere acción inmediata en la Fase 1 del plan de remediación.

**Archivos a modificar:**
- `custom_addons/madenat_lumber_core/views/guia_processing_views.xml` (2 cambios)
- `custom_addons/madenat_lumber_core/views/guia_processing_list_search.xml` (5 cambios)
- `custom_addons/madenat_lumber_core/views/lumber_core_menu.xml` (1 cambio)

**Tiempo estimado de implementación:** 30 minutos para cambios + 1 hora de pruebas en staging.
**Ventana recomendada:** Mantenimiento programado, no requiere migración de datos.
**Rollback:** Inmediato revirtiendo los archivos a su estado actual (todos los cambios son en XML de vistas/acciones, no en datos ni estructura).

---

*Informe generado por auditoría técnica automatizada el 2026-06-19. Versión 1.0.*