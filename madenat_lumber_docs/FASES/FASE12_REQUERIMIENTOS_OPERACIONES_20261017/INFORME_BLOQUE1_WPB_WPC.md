# INFORME BLOQUE 1 — FASE 12 (WP-C y WP-B Rótulos)
**Fecha:** 2026-10-17 | **Agente:** Antigravity | **Estado:** CHECKPOINT BLOQUE 1 COMPLETADO

---

## 1. Resumen Ejecutivo de Cambios

En cumplimiento con la aprobación de Mauricio para la Compuerta E2 / Etapa E3 (Bloque 1), se implementaron exclusivamente los paquetes:

1. **WP-C:** Búsqueda y menú dedicado «Ingresos por Volúmenes» con soporte completo de filtros por Guía, Proveedor y Estado.
2. **WP-C (Investigación D-E0-3):** Diagnóstico de causa raíz por la cual la guía 95806 (JCE) quedó con proveedor "S.I.I. - LOS ANGELES", propuesta técnica y opciones para regularizar sin tocar datos existentes.
3. **WP-B Rótulos:** Unificación canónica de los rótulos de volumen en las vistas de Embarque y Contenedor («Vol. Compra (m³)», «Vol. Export (m³)» y «Vol. Documental (m³)`).

### Módulos Modificados y Versiones Monótonas
- `madenat_lumber_intake`: `18.0.0.15.0` → `18.0.0.16.0` (CHANGELOG actualizado).
- `madenat_lumber_logistics`: `18.0.1.36.0` → `18.0.1.37.0` (CHANGELOG actualizado).
- `madenat_lumber_docs`: Canon `04_DECISION_LOG.md` actualizado con decisión **AD-111**.

---

## 2. Detalle Paquete 1: WP-C (Consola y Menú de Volúmenes)

### Cambios Realizados
1. **Vista de Búsqueda:** En `madenat_lumber_intake/views/intake_console_views.xml`, se agregó el campo `<field name="state" string="Estado"/>` y se renombró el filtro preconfigurado `type_volume` a «Ingresos por Volúmenes».
2. **Acción Dedicada:** Se definió la acción `action_madenat_lumber_intake_console_volume` sobre `madenat.lumber.intake.console`, con dominio `[('ingestion_type', '=', 'volume')]` y contexto `'search_default_type_volume': 1`.
3. **Menú Operativo:** En `madenat_lumber_intake/views/intake_menus.xml`, se agregó la entrada de menú `menu_madenat_lumber_intake_volume` («Ingresos por Volúmenes») bajo la rama canónica de recepción:
   `MADENAT Lumber → Operaciones → Abastecimiento → Gestión de Entradas` (secuencia 2, grupo `group_madenat_operaciones`).
4. **Pruebas Automatizadas (TDD):** Nueva suite `madenat_lumber_intake/tests/test_volume_console_search_menu.py` con 4 pruebas aprobadas en verde.

---

## 3. Investigación D-E0-3: Guía 95806 (JCE) con Proveedor "S.I.I."

### Hallazgo y Causa Raíz
1. **Naturaleza del Documento:** Al inspeccionar `GDE 95806.pdf`, se constató que el logo/membrete de JCE en la parte superior izquierda es una imagen gráfica raster (`Im1`), carente de capa de texto seleccionable.
2. **Extracción en Timbre DTE:** En la esquina superior derecha del PDF se ubica el timbre reglamentario del SII con el texto:
   ```
   R.U.T.: 96.547.890-6
   GUÍA DE DESPACHO
   ELECTRÓNICA
   Nº 95806
   S.I.I. - LOS ANGELES
   ```
3. **Falla en el Parser:** `_find_emitter_company_name()` en `madenat_guia_processing.py` descarta términos como `GUÍA`, `DESPACHO`, `ELECTRÓNICA`. Sin embargo, la línea `S.I.I. - LOS ANGELES` fue evaluada como válida porque `ANGELES` no pertenece a la lista de palabras reservadas.
4. **Creación Automática:** Como el RUT `96.547.890-6` no existía previamente en la base de datos, `_resolve_or_create_supplier()` ejecutó `auto_create` creando el registro `res.partner` ID 2417 con nombre `"S.I.I. - LOS ANGELES"` y VAT `"96.547.890-6"`.
5. **Comportamiento Actual:** Cada vez que el sistema procesa un documento con RUT `96.547.890-6`, resuelve inmediatamente el partner 2417 por coincidencia exacta de VAT.

### Opciones de Corrección (Sin alterar datos actuales)
- **Opción 1 (Recomendada - Corrección de Datos vía Interfaz):**
  Un usuario con permisos de administración/operaciones edita el contacto `res.partner` ID 2417 desde la interfaz de Odoo y cambia su nombre de `"S.I.I. - LOS ANGELES"` a `"JCE S.A."` (o la razón social formal requerida). Al mantener el mismo ID y VAT, todas las guías pasadas y futuras quedarán asociadas limpiamente al proveedor correcto.
- **Opción 2 (Blindaje del Parser para Futuros Documentos):**
  Añadir un filtro en `_find_emitter_company_name()` que descarte líneas que comiencen o contengan `S.I.I.` o patrones de direcciones regionales del SII (`r'^S\.?I\.?I\.?'`), de modo que no se generen nombres erróneos ante emisores con logo gráfico.

---

## 4. Detalle Paquete 2: WP-B Rótulos (Unificación de Volúmenes)

### Problema Resuelto
Existían etiquetas inconsistentes entre vistas («Vol. Físico», «Vol. Emb.», «Vol. Nominal (m³)», «m³ Embarque», «Volumen Exportación (facturable)»), y la grilla de lotes de contenedor mostraba `volumen_m3` en lugar del volumen de compra de la etiqueta.

### Homologación Aplicada
1. **«Vol. Compra (m³)»:** Asignado canónicamente al volumen de compra por etiqueta (`volume_purchase_m3`) y a los totales derivados (`total_volume_purchase_m3`, `total_nominal_volume_m3`, `physical_volume_m3`).
2. **«Vol. Export (m³)»:** Asignado canónicamente al volumen de exportación/embarque (`vol_shipment_m3`, `total_vol_shipment_m3`, `volume_m3`, `total_volume_m3`, `export_volume_m3`).
3. **«Vol. Documental (m³)»:** Claramente diferenciado en las vistas de imputación documental SV (`sv_assignment_nominal_m3`, `sv_ret_nominal_m3`).
4. **Vistas Actualizadas:**
   - `lumber_container_views.xml` (lista, formulario y grilla de lotes).
   - `lumber_container_lot_wizard_views.xml` (asistente de selección y export list).
   - `lumber_export_shipment_views.xml` (pivot, lista, formulario, contenedores y auditoría de cálculo).
   - `madenat_sv_imputation_views.xml` (lista de etiquetas SV, pestaña de guías e imputaciones).
5. **Pruebas Automatizadas (TDD):** Nueva suite `madenat_lumber_logistics/tests/test_volume_labels_unification.py` con 5 pruebas en verde.

---

## 5. Respaldo y Evidencia de Seguridad

1. **Respaldo Pre-Edición:** Copia íntegra de archivos originales en:
   `/home/viruco/dev-stack/odoo/odoo-18-ce/FASE12_REQUERIMIENTOS_OPERACIONES_20261017/respaldos/pre_bloque1_20261017_145310/`
2. **Commits Locales con Rutas Explícitas:**
   - Commit `55579bd`: `feat(intake): búsqueda y menú dedicado Ingresos por Volúmenes (WP-C / FASE 12)`
   - Commit `e189a22`: `feat(logistics): unificar rótulos de volumen en embarque y contenedor (WP-B rótulos / FASE 12)`
   - Commit `74bf4e8`: `docs(canon): AD-111 operaciones bloque 1: consola e ingresos por volúmenes y unificación de rótulos`
3. **Aislamiento Estricto:**
   - Sin push, sin remoto.
   - `madenat_lumber_costing` y `madenat_lumber_reports` no fueron tocados ni incluidos en ningún commit.
   - Datos reales (`IMP04823`, `IMP02220`) intactos.
