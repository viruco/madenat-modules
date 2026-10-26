# INFORME DE DESCUBRIMIENTO — E1
**FASE 12 — Requerimientos de Operaciones (Cristhian)**  
**Fecha:** 2026-10-17 | **Agente:** Antigravity | **Solo lectura — cero cambios**

---

## WP-C — VISIBILIDAD DE INGRESOS POR VOLÚMENES E INVENTARIOS (R4)

### C.1 Cómo entra una guía por modalidad Volúmenes

La modalidad se llama internamente **`granel`** (no "Volúmenes") en el campo
`madenat_guia_processing.tipo_recepcion`:

```
madenat_guia_processing.py:611
    tipo_recepcion = fields.Selection([
        ...
        ('granel', 'Recepción por Volumen')
```

El flujo de ingreso:
1. **Wizard de Ingreso de Madera** (`madenat_lumber_intake`) → crea registro `madenat.guia.processing` con `tipo_recepcion='granel'`.
2. Si el ingreso es por volumen sin detalle de piezas, se crea una **línea de resumen sintética** via `_create_granel_summary_line()` (`madenat_guia_processing.py:1304`).
3. Si el PDF/Excel contiene líneas de detalle, se usa `_create_granel_detail_lines()` (`madenat_guia_processing.py:1366`).
4. La guía NO pasa por el motor de recepción físico de Odoo (no hay picking de entrada desde proveedor). `tipo_recepcion='granel'` está en `_B1_EXCLUDED_TIPOS` (`madenat_guia_processing.py:1552`), así su movimiento lo consume cuando se asigna a un lote de patio.
5. La **consola de intake** (`madenat.lumber.intake.console`) es una vista SQL (VIEW, no modelo ORM persistente). Expone las guías `granel` con `ingestion_type = 'volume'`.

### C.2 Dónde se ven hoy las guías ingresadas

La consola de intake es accesible desde:
- **Menú:** `MADENAT Lumber → Operaciones → Abastecimiento → Gestión de Entradas → Ingreso de Madera`
  - `intake_menus.xml`: `menu_madenat_lumber_intake_wizard` → `action_madenat_lumber_intake_console`
  - Solo visible al grupo `group_madenat_operaciones`.
- **Menús de Jefatura:** Ingreso de Guías y Guías Procesadas (restringidos a `group_madenat_jefatura_operaciones`).

**El filtro por modalidad existe** (`ingestion_type = 'volume'` en la vista SQL,
expuesto como campo filtrable). Sin embargo, **Cristhian no lo encuentra** porque:
1. El campo en la consola no tiene un **filtro preconfigurado visible** por "Ingreso por Volúmenes".
2. La búsqueda por número de guía **sí funciona** si el operador lo conoce, pero no hay un acceso directo con el nombre "Ingresos por Volúmenes".
3. Los menús de Jefatura (guías procesadas) requieren permisos que Cristhian puede no tener o no conocer.

### C.3 Guías Arauco 4495589 y JCE 95806 en madenat_test

**CONFIRMADO EN DB LOCAL:**
```sql
-- Resultado de SELECT g.name, g.tipo_recepcion, g.state, r.name FROM madenat_guia_processing
  name     | tipo_recepcion | state     | proveedor
-----------+----------------+-----------+------------------------
 4495589   | granel         | validated | Maderas Arauco S.A.
 95806     | granel         | verified  | S.I.I. - LOS ANGELES
```

**Ambas guías existen en madenat_test.** Están también en la consola de intake:
```sql
-- madenat_lumber_intake_console:
 guide_name | ingestion_type | state     | source_model
 4495589    | volume         | validated | madenat.guia.processing
 95806      | volume         | verified  | madenat.guia.processing
```

**Causa por la que no se "encuentran":** la consola muestra todas las modalidades
mezcladas. No hay una entrada de menú separada para "Ingresos por Volúmenes".
Además, la guía 95806 tiene como partner `S.I.I. - LOS ANGELES` (no "JCE"),
lo que dificulta buscarla por proveedor. [CONFIRMAR: ¿el partner real de JCE es S.I.I.?]

### C.4 Inventarios — dónde visualizar

- **Vista de lotes:** `stock_lot_views.xml` en `madenat_lumber_core`. Accesible desde `Operaciones → Inventario → Etiquetas SV`.
- **Vista de quants (saldo físico):** vista nativa `stock.quant` con herencia en `madenat_processor_balance_views.xml` (solo lectura, para procesadores).
- **Agrupación por ubicación:** no existe una vista de inventario agrupada por patio (MARVAL, Bodega Tepornac, PUERTO CORONEL) en el código actual. Solo la lista de quants tiene el campo `location_id` visible.
- **Faltan:** acceso directo a inventario por patio; vista kanban o pivot de stock.lot por ubicación.

### C.5 Propuesta mínima (para PLAN_FASE12)

1. Filtro preconfigurado "Ingresos por Volúmenes" en la consola de intake (una línea XML).
2. Entrada de menú opcional "Ingresos por Volúmenes" como submenú del módulo de intake.
3. Vista de inventario agrupada por ubicación (stock.quant o stock.lot) — nueva vista de lista con groupby `location_id`.
4. Corrección del partner de guía 95806: [CONFIRMAR con Mauricio antes de tocar datos].

---

## WP-D — PATIOS (R5)

### D.1 Estructura de ubicaciones (stock.location) — evidencia DB

```sql
-- Resultado de SELECT name, complete_name, usage FROM stock_location WHERE active=true
  id  | name                 | complete_name                          | usage
------+----------------------+----------------------------------------+------------
    8 | Stock                | WH/Stock                               | internal
   19 | Bodega Tepornac      | WH/Stock/Bodega Tepornac               | internal
   18 | MARVAL               | WH/Stock/MARVAL                        | internal
 4918 | Procesadores         | WH/Stock/Procesadores                  | internal
 4919 | V3 Planta (temp)     | WH/Stock/Procesadores/V3 Planta (temp) | internal
   17 | PUERTO CORONEL       | WH/Stock/PUERTO CORONEL                | internal
```

**Hallazgo crítico:** No existe ninguna ubicación llamada "Patio Servicio Cepillado Ferramenta" ni "Patio Marval" (con ese nombre). Existen:
- **MARVAL** (id=18): ubicación interna. Es el "Patio Marval" del negocio.
- **PUERTO CORONEL** (id=17): ubicación interna. Podría ser el "patio de puerto".
- **Bodega Tepornac** (id=19): ubicación interna. Posible bodega de servicio/cepillado.
- **Procesadores** (id=4918): destino para guías de procesado.

### D.2 Cómo se asigna la ubicación en el ingreso

En `madenat_guia_processing.py:2563–2617`:
1. Si `assignment_location_id` está definido → se usa esa ubicación.
2. Si no → `picking_type.default_location_dest_id`.
3. Fallback: búsqueda en `stock.location` con `usage='internal'` y `complete_name LIKE '%WH/Stock%'`.

El campo `assignment_location_id` (línea 763 del mismo modelo) es `Many2one('stock.location')` y permite al usuario elegir el patio manualmente.

**Para guías `granel`**: el flujo es distinto. El guía granel NO crea un picking de recepción propio; su volumen queda en un lote de "patio" (stock.lot) que luego se consume cuando se asigna al embarque (AD-69). La ubicación del lote granel se define implícitamente por la guía/proveedor.

### D.3 Quants por ubicación

```sql
-- stock_quant con qty>0 agrupados por ubicación (evidencia):
 location_name  | count | qty total (aprox)
 Customers      |   5   | (UAT + SV test + UATRB)
 Stock (WH)     |  ~100 | (la mayoría de lotes de producción)
```

No hay quants en MARVAL, PUERTO CORONEL ni Bodega Tepornac con cantidades positivas en madenat_test. Todos en `WH/Stock`.

### D.4 Impacto sobre trazabilidad

- Las **rebajas SV** (`madenat.sv.imputation`) no tienen campo de ubicación de origen; operan sobre el lote (stock.lot) por su disponibilidad documental.
- Las **imputaciones** (IMP02220, etc.) están ligadas al lote SV, no a la ubicación directamente.
- Cambiar la ubicación de los lotes existentes requeriría movimientos de inventario, con impacto en trazabilidad y potencial en la lógica de rebaja.
- **Implicación contable:** las ubicaciones en Odoo CE no tienen cuentas asignadas por defecto; si se usa la valoración de inventario (FIFO/AVCO), mover entre ubicaciones internas no genera asiento contable. [CONFIRMAR política con Contabilidad antes de crear ubicaciones nuevas].

### D.5 Propuesta mínima

Requisito R5 pide separar "Patio Servicio Cepillado Ferramenta" de "Patio Marval".  
Propuesta mínima (pendiente de confirmación de nombres con Cristhian):
1. Renombrar/reclasificar ubicaciones existentes (MARVAL → "Patio Marval / Puerto", Bodega Tepornac → "Patio Ferramenta / Cepillado") O crear dos ubicaciones nuevas.
2. Datos maestros vía `data/` con `noupdate="1"` (no scripts manuales).
3. Campo `location_type` o categoría en `stock.location.category` para clasificar "patio de servicio" vs "patio de puerto".
4. Política de ubicación por defecto según `tipo_recepcion` (granel → Ferramenta/Cepillado; puerto/embarque → Marval).
5. [CONFIRMAR] nombres exactos con Cristhian antes de implementar.

---

## WP-B — PANTALLA DE EMBARQUE: RÓTULOS Y ANCHO EXPORT (R2, R3)

### B.1 Localización de la pantalla de embarque

- **Modelo principal:** `lumber.export.shipment` (`madenat_lumber_logistics/models/lumber_export_shipment.py`)
- **Vista principal:** `lumber_export_shipment_views.xml`
- **Contenedor hijo:** `lumber.container` → `lumber_container_views.xml`
- **Lote (etiqueta):** `stock.lot` con extensiones en `stock_lot_views_inherit.xml`

### B.2 Los tres volúmenes — evidencia en código

| Nombre | Campo | Modelo | Archivo:Línea |
|---|---|---|---|
| **Vol. Compra (documental)** | `volume_purchase_m3` en `stock.lot` | `stock.lot` | `stock_lot.py:~485` |
| **Vol. Embarque (packing)** | `vol_shipment_m3` | `stock.lot` | `stock_lot.py:453` |
| **Vol. Nominal (contenedor)** | `total_volume_purchase_m3` | `lumber.container` | `lumber_container.py:130` |
| **Vol. Exportación (facturable)** | `total_vol_shipment_m3` | `lumber.container` | `lumber_container.py:121` |

**En las vistas del contenedor** (`lumber_container_views.xml:154–171`):
```xml
<field name="total_vol_shipment_m3" string="Vol. Exportación (m³)"/>
<field name="total_volume_purchase_m3" string="Vol. Nominal (m³)"/>
<field name="vol_shipment_m3" string="Vol. Emb." />  <!-- por lote, línea 428 -->
<field name="volumen_m3" string="Vol. Físico" />     <!-- por lote, línea 427 -->
```

**En el embarque** (`lumber_export_shipment_views.xml:213–255`):
```xml
<field name="total_volume_m3" string="Vol. de Embarque Total (m³)"/>
<field name="total_nominal_volume_m3" string="Vol. Físico Total (m³)"/>
<field name="volume_m3" string="Vol. Exportación (m³)"/>
<field name="export_volume_m3" string="Vol. Facturable (m³)"/>
```

**Diagnóstico R2:** Hay múltiples etiquetas inconsistentes:
- "Vol. Físico Compra (m³)" vs "Vol. Nominal (m³)" vs "Vol. de Embarque Total (m³)" — no está claro cuál es el "volumen de compra por etiqueta" que pide Cristhian.
- "Vol. M³" que menciona Cristhian probablemente es `vol_shipment_m3` (el de packing/embarque comercial).
- El "volumen comercial 48,009" es el `total_vol_shipment_m3` del embarque calculado con dimensiones de exportación (espesor + ancho S2S + largo × piezas / 1.000.000).

### B.3 Ejemplo guía 26270 (evidencia histórica)

Del INDICE y respaldos:
- Vol. documental/guía: **57,8400 m³** (`official_volume_m3` en guía)
- Vol. packing (suma de detalle): **57,839556 m³** (`volume_detail_m3` en guía)
- Vol. embarque comercial: **48,009 m³** (`vol_shipment_m3` calculado con dimensiones S2S)

La diferencia 57,8400 vs 57,839556 = **0,000444 m³ ≈ 0,001 (tercer decimal)**. Esto confirma R1: diferencias en décimas de milímetro que no son relevantes.

### B.4 Ancho Export — por qué 150mm no produce 5 5/8" (R3)

**Evidencia encontrada:**

```python
# width_mapping.py:31
MAPPING = {
    ...
    150:  (5.625, "5 5/8"),   # ← LA EQUIVALENCIA EXISTE
    ...
}
```

**El MAPPING hardcode sí tiene 150 mm → 5.625" = "5 5/8".**

Pero la función `get_s2s_adjustment()` (`utils_uom.py:886`) **no** devuelve el ancho exportación; devuelve el **ajuste +1/8" sobre el ancho rough**. El ancho de exportación real se calcula en `_compute_vol_shipment_m3()` (`stock_lot.py:470`):

```python
# stock_lot.py:508-509
if lot.ancho_nominal_mm > 0:
    a_in = lot.ancho_nominal_mm / MM_PER_INCH
else:
    a_in = lot.product_id.commercial_width_mm if is_std else lot.ancho_mm
```

Luego: `overmeasure = get_s2s_adjustment(env, a_mm)` que retorna `Decimal('0.125')` si no está en la lista de exclusiones, y se suma: `a_export = a_in + overmeasure`.

**Para 150mm:**
- 150mm ÷ 25.4 = 5.9055"
- +0.125" (S2S) = 6.0305" ≈ 6 1/32" (NO es 5 5/8")

**El problema**: 150mm **rough** (antes de cepillar) produce 5 5/8" S2S según la tabla del negocio, pero el sistema calcula `150/25.4 + 0.125 = 6.03"`. La tabla `lumber.width.s2s.map` existe exactamente para resolver esta conversión rough→S2S, pero **no se usa en `_compute_vol_shipment_m3()`** para el ancho de exportación. El sistema aplica la conversión lineal directa + ajuste plano, ignorando la tabla.

**Hay tres fuentes de la tabla:**
1. Modelo persistente `lumber.width.s2s.map` (registro en DB, configurable) — prioridad 1
2. `ir.config_parameter 'madenat.width_s2s_map'` — prioridad 2 (fallback)
3. `WidthMappingTable.MAPPING` hardcode (`width_mapping.py`) — prioridad 3

`_compute_vol_shipment_m3()` usa `get_s2s_adjustment()` que **solo devuelve 0.0 o 0.125** (sin/con recargo), pero **no hace la conversión nominal→S2S**. La tabla rough→S2S está definida pero no aplicada en el cálculo de volumen de embarque.

### B.5 Propuesta mínima

1. Rótulos claros en las vistas de embarque/contenedor (cambios XML mínimos, sin lógica).
2. Campo `vol_compra_m3` por lote en la pantalla del contenedor — el campo `volume_purchase_m3` ya existe; solo falta rótulo claro "Vol. Compra (m³)".
3. Uso de la tabla `lumber.width.s2s.map` en `_compute_vol_shipment_m3()` para obtener el ancho S2S real a partir del `ancho_mm` rough.
4. Campo manual de ancho S2S con campo de auditoría (usuario + timestamp) para anchos superiores no en la tabla.
5. [CONFIRMAR] la tabla completa de equivalencias con Cristhian y Mauricio. Solo 150mm=5 5/8" está confirmado.

---

## WP-A — VOLÚMENES GUÍA VS PACKING (R1)

### A.1 Cómo se calcula y compara hoy

En `madenat_lumber_core/models/madenat_guia_processing.py`:
- `volume_excel_m3`: volumen leído del Excel/PDF de la guía.
- `volume_detail_m3`: suma de las líneas de detalle del packing list.
- `official_volume_m3`: campo unificado de volumen oficial de la guía.
- `conciliation_status`: estado de conciliación (selección con opciones como `ok_exact`, `needs_manual_review`, `incompatible`, `not_compared`).

En `madenat_lumber_intake/models/intake_console.py:804`:
```python
rec.volumen_diff_m3 = round(
    (official_volume_m3 - volume_detail_m3), ...)
```

La comparación actual usa la precisión implícita de Float; no hay una regla explícita de "comparar a 3 decimales y no alertar si la diferencia es solo de decimales".

**El campo `conciliation_status` en `madenat_guia_processing.py`** usa opciones como `needs_manual_review` que se activan si la diferencia supera cierto umbral. El umbral exacto NO se encontró en el grep (el campo `_compute_conciliation` no aparece en la búsqueda, podría estar inline).

### A.2 Ejemplo guía 26270

| Fuente | Valor | Precisión |
|---|---|---|
| Guía (PDF) | 57,8400 m³ | 4 decimales (2 significativos) |
| Packing (detalle) | 57,839556 m³ | 6 decimales |
| Diferencia | 0,000444 m³ | irrelevante para Cristhian |
| A 3 decimales | 57,840 vs 57,840 | iguales → sin alerta |

### A.3 Propuesta mínima

1. Agregar comparación a 3 decimales (`round(x, 3) == round(y, 3)`) como condición de "ok_rounded".
2. Si la diferencia redondeada es cero → `conciliation_status = 'ok_rounded'` (sin alerta).
3. El packing prevalece como valor operativo (`volume_detail_m3` → `official_volume_m3`).
4. La regla exacta queda [CONFIRMAR] con Cristhian (¿qué pasa si la guía trae 2 decimales: 57,84 vs 57,839556?).

---

## WP-E — PLANTILLA DE PACKING (R6)

### E.1 El lector que funciona — Forestal Andes

El motor de ingesta (`madenat_ingestion_engine`) define perfiles en `ingestion_profiles.py`. Los perfiles confirmados son:

**`PACKING_METRICO_ASERRADA`** (madera seca cepillada, sistema métrico):
- Columnas: `N° PQTE | CODIGOS | PRODUCTO | ESPESOR MM | ANCHO MM | LARGO MM | FILAS | COLUMNAS | PIEZAS | VOLUMEN M3 | LOTE`
- Unidades: mm/m
- Síntesis: lote por `product_code`
- Forward-fill: campo `lot_number`

**`PACKING_IMPERIAL_BLANKS`** (blanks clear, sistema imperial):
- Similar pero en pulgadas/pies.

**Arauco** usa formato PDF con tabla genérica; su fixture es `HLZF75_4495589.pdf` (byte-idéntico). El lector de PDF genérico funciona.

**Para Fátima 41994 y BYC 95083:** R6 indica que solo requieren un packing en el formato que el sistema ya reconoce (PACKING_METRICO_ASERRADA o PACKING_IMPERIAL_BLANKS). Los datos originales de Fátima 41994 existen en DB (`state=verified`, recepción 7950). BYC 95083: no se encontró en la búsqueda inicial.

### E.2 Entregables propuestos

1. **Plantilla XLSX** basada en `PACKING_METRICO_ASERRADA` con las columnas exactas, encabezados validados por el perfil, y hoja de instrucciones.
2. **Guía de llenado** (1 página): reglas por columna, ejemplos de valores, errores comunes.
3. **Pruebas sintéticas** con datos de ejemplo que demuestren que el lector actual las acepta.
4. NO desarrollar lectores para Arauco, JCE, BYC. [CONFIRMAR] si los datos originales de BYC 95083 están disponibles.

---

## WP-F — REBAJA DE VOLUMEN EN EMBARQUES Y TARJAS (R7)

### F.1 Estado real de la rebaja

El flujo de rebaja SV está implementado en `madenat.sv.imputation` (modelo) y `madenat_sv_imputation_wizard` (wizard):

| Componente | Estado |
|---|---|
| Modelo `madenat.sv.imputation` | ✅ Implementado (AD-91, AD-110) |
| Wizard de rebaja (`madenat_sv_imputation_wizard.py`) | ✅ Implementado |
| Flujo draft→applied→reversed | ✅ Con guardas de ciclo de vida (FASE11) |
| Clave documental (`documentary_key`) | ✅ (FASE10) |
| Guarda de guardado vacío | ✅ (FASE10, S3) |
| Selección de etiquetas sin saldo | ⚠️ PENDIENTE (AUDITORIA_DISPONIBILIDAD_ETIQUETAS, P1–P5) |

### F.2 Respuesta de estado para Cristhian ("¿en qué están las tarjas?")

> **La rebaja de etiquetas SV existe y funciona en el sistema.**
> - Se accede desde: `MADENAT Lumber → Logística → Rebaja de Etiquetas`
> - El flujo es: seleccionar etiquetas disponibles → preparar el reparto por SV → aplicar → quedar registrado con motivo.
> - Las tarjas de consolidación (agrupación de etiquetas en un contenedor/SV) se registran a través de este asistente.
>
> **Lo que falta (PENDIENTE, pendiente de aprobación):**
> - P1: El formulario permite seleccionar etiquetas sin saldo (etiquetas que ya fueron imputadas o no tienen volumen disponible). Esto confunde al operador.
> - P2–P5: "Seleccionar todas" incluye etiquetas no disponibles; la sección de solo lectura para las no disponibles aún no existe; el resumen no es coherente con la selección real.
> - IMP02220: guía aplicada sin reparto, bloquea D7632 y D7642 en SV00000000841. La decisión de negocio está pendiente (excepción histórica o reversa oficial).

### F.3 Propuesta P1–P5 (planificación, sin implementar)

| ID | Descripción | Esfuerzo |
|---|---|---|
| P1 | Filtrar etiquetas seleccionables a solo las disponibles en el wizard | S |
| P2 | Limitar "Seleccionar todas" a etiquetas disponibles | S |
| P3 | Sección de solo lectura para etiquetas no disponibles con su documento | M |
| P4 | Resumen coherente (muestra solo disponibles en el conteo activo) | S |
| P5 | Mensaje que nombre etiquetas y documentos bloqueantes | S |
| P6 | Diferido por decisión de negocio | — |

### F.4 IMP02220 — Opciones de negocio

| Opción | Descripción | Riesgo |
|---|---|---|
| A | Excepción histórica: documentar como caso especial, no modificar | Mínimo |
| B | Reversa oficial con motivo por Jefatura | Requiere autorización y desbloquea D7632/D7642 |

Propuesta: presentar a Mauricio y Cristhian para que elijan. Ninguna se implementa sin aprobación.

---

## WP-G — ALINEACIÓN DOCUMENTAL Y HOJA DE RUTA (R8)

### G.1 Desalineaciones documento↔código

| Documento | Versión | Desalineación |
|---|---|---|
| `HOJA_RUTA_EJECUTIVA.md` | 2026-05-23 | Menciona prioridades pre-FASE10 (largo/unidades, T29–T32). No refleja R1–R8 ni FASE12. |
| `_CAPSULA_CONTEXTO.md` | 2026-05-30 | Costing/reports como "pendiente de inventario"; grupos de seguridad incompletos. |
| `INDICE_DOCUMENTACION.md` | 12.37.0 | Línea 106 dice versión `12.13.0` en la tabla (el encabezado dice `12.37.0`). Inconsistencia menor. |
| `CANON/00_ARQUITECTURA.md` | 7.18.0 (2026-10-07) | No menciona arquitectura de Fase 12 ni requisitos de Cristhian. |
| `CANON/05_BACKLOG.md` | 8.18.0 (2026-10-10) | No incluye WP-A…G de la FASE 12. |

### G.2 Roadmap por paquete (para PLAN_FASE12)

Ver documento PLAN_FASE12.md.

---

## Resumen de Evidencia por Requisito

| Req | Paquete | Estado | Evidencia |
|---|---|---|---|
| R1 | WP-A | Parcial — falta regla de 3 decimales | `intake_console.py:804`, `madenat_guia_processing.py:conciliation_status` |
| R2 | WP-B | Parcial — rótulos inconsistentes | `lumber_container_views.xml:154–171`, `lumber_export_shipment_views.xml:213–255` |
| R3 | WP-B | Defecto identificado — tabla S2S no usada en cálculo | `stock_lot.py:470–560`, `width_mapping.py:31`, `utils_uom.py:886` |
| R4 | WP-C | Problema de UX — guías existen en DB, no hay filtro visible | DB: guías 4495589/95806 en consola con `ingestion_type=volume` |
| R5 | WP-D | Gap — ubicaciones existen pero no clasificadas | DB: MARVAL, PUERTO CORONEL, Bodega Tepornac; sin "Ferramenta" |
| R6 | WP-E | Lector existe; falta plantilla y guía de llenado | `ingestion_profiles.py`: PACKING_METRICO_ASERRADA |
| R7 | WP-F | Modelo implementado; P1–P5 pendientes; IMP02220 bloqueado | `madenat_sv_imputation_wizard.py`, AUDITORIA_DISPONIBILIDAD_ETIQUETAS |
| R8 | WP-G | Desalineaciones detectadas en HOJA_RUTA y CAPSULA | Ver G.1 |

