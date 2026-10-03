# Reporte de investigación: patrón robusto para números de lote repetidos
### Recepción directa vs Procesados — Odoo 18 CE / MADENAT

---

## 1. Resumen ejecutivo

**Diagnóstico confirmado.** En la recepción directa **15183** (`lumber.reception` id 1369, estado `verified`), el Gate 3 falla con `IntegrityError` de la restricción estándar de Odoo `UNIQUE(product_id, name, company_id)` de `stock.lot`. No existe ningún `stock.lot` persistido llamado `0000000000446` antes ni después del error (verificado por ORM: `lot_count = 0`). La colisión es **intra-transacción**: dos líneas de staging distintas intentan crear el **mismo** `stock.lot` dentro del mismo flujo.

**Causa raíz (hecho confirmado, no hipótesis).** `LumberReceptionService.create_lots_from_staging` (`reception_service.py:17-102`) construye un índice local `existing_index` **una sola vez** a partir de los lotes ya persistidos (vacío para una recepción nueva) y **no lo actualiza** después de cada `stock.lot.create()` dentro del bucle. Dos líneas con la misma clave `(name, product_id)` caen ambas en la rama `create` → colisión `UNIQUE` → el error se envuelve como `"🛑 Error en el motor de inventario: ..."` (`action_confirm_reception`, `lumber_reception.py:2876-2878`).

**Naturaleza del packing (hecho confirmado).** Las líneas 4809 y 4810 comparten `lot_name`, producto, subproducto, espesor y ancho; difieren solo en **largo** (4,05 m vs 3,70 m), **piezas** (240 vs 50) y **volúmenes** (3,596 m³ vs 0,685 m³). Es un **lote lógico con composición dimensional múltiple** legítimo, no un duplicado documental accidental.

**Recomendación preliminar (una línea).** Adaptar los principios del patrón `_create_or_get_lot` de Procesados (búsqueda previa + `savepoint` + re-búsqueda + reutilización idempotente) al servicio de recepción, **agrupando** el staging por clave de identidad `(name, product_id)`, creando **un** `stock.lot` por grupo y preservando cada fila del packing como una `stock.move.line` distinta (para no perder la composición 240×4,05 m + 50×3,70 m).

---

## 2. Alcance y salvaguardas

**No se modificó** código, XML, datos, módulos, configuración, ni se ejecutaron acciones de negocio. Solo lecturas ORM/SQL (`search`, `browse`, `read`, `search_count`), inspección de código y `git` en modo consulta.

Fuera de alcance (no analizado ni propuesto): fórmulas S2S/Blank/metric, UoM/volúmenes/costos/nominales, maquila/toll processing, consumo/reversión/contenedores/embarques/facturación, parsing documental, `madenat_lumber_intake` (fachada), datos maestros y configuración.

---

## 3. Evidencia de entorno

| Elemento | Valor |
|---|---|
| Base activa | `madenat_test` (`db_name = madenat_test`, `db_user = odoo`, `db_host = db`, `db_port = 5432`) |
| Contenedor Odoo | `odoo18_app` (servicio `web`), `python3 /usr/bin/odoo --config /etc/odoo/odoo.conf --database madenat_test --dev=reload,qweb,werkzeug` |
| Contenedor PostgreSQL | `odoo18_db` (servicio `db`), Postgres 15, healthy |
| Rama Git | `backup/wip-20260819-intake-alignment` |
| HEAD | `aab1b46 docs(madenat): documentar contrato de ingesta y volúmenes` |
| Código custom | `/mnt/extra-addons` (host `~/dev-stack/odoo/odoo-18-ce/custom_addons`) |

`git status --short` muestra cambios **sin commitear** previos a esta investigación (módulos `madenat_lumber_intake`, `madenat_lumber_logistics`, `madenat_lumber_purchasing` y directorio `madenat_ingestion_engine/` sin trackear). **Ninguno** de esos archivos productivos fue alterado en esta investigación.

---

## 4. Caso reproducible 15183

Recepción `lumber.reception(1369)` — nombre `15183`, `state=verified`, `ingestion_profile=metric`.

| Atributo | Línea 4809 | Línea 4810 | ¿Difiere? |
|---|---|---|---|
| `lot_name` | `0000000000446` | `0000000000446` | no |
| `product_id` | 166 (`[MADERA_ASERRADA_SECA] Madera Aserrada Seca`) | 166 | no |
| `subproduct_id` | 625 (`COL A`) | 625 | no |
| `thickness` | 37,0 mm | 37,0 mm | no |
| `width` | 100,0 mm | 100,0 mm | no |
| `thickness_nominal` | 37,0 | 37,0 | no |
| `width_nominal` | 100,0 | 100,0 | no |
| `length` | **4,05 m** | **3,70 m** | **sí** |
| `pieces` | **240** | **50** | **sí** |
| `vol_purchase_m3` | **3,596** | **0,685** | **sí** |
| `vol_shipment_m3` | 3,596 | 0,685 | sí |
| `length_input_raw` | 4,05 | 3,70 | sí |
| `lengthuom` | `m` | `m` | no |
| `export_calculation_rule` | `metric` | `metric` | no |

**Cálculo de volúmenes (comprobación):**
- 4809: `(37/1000) × (100/1000) × 4,05 × 240 = 3,5964 m³` → `3,596` ✓
- 4810: `(37/1000) × (100/1000) × 3,70 × 50 = 0,6845 m³` → `0,685` ✓

**Consecuencias:**
- No existe `stock.lot` persistido (`name=0000000000446`, `product_id=166`): `search_count = 0`.
- Auditoría de la recepción: solo 1 evento `creation` (origen intake). **No** hay `lot_creation`/`lot_update` porque el Gate 3 abortó antes de auditar lotes.
- Producto 166: `tracking='lot'`, `company_id=False` (producto compartido).

---

## 5. Patrón actual de Procesados

**Método núcleo:** `madenat.guia.processing._create_or_get_lot` — `madenat_guia_processing.py:3570`.

**Diagrama de secuencia (simplificado):**

```
action_validate (1543) → do_full_processing (946)
  → por cada item: _create_or_get_lot (1023)
      ├─ normalizar name (3608)
      ├─ flush_model(name, product_id, company_id) (3614)
      ├─ SEARCH: name + product_id + company_id in [company, False]
      │          + reception_id = False            (3616-3621)
      ├─ armar vals (dims, volúmenes, guia_processing_id,
      │             reception_id=False, visuales, estados) (3626-3702)
      ├─ si lot encontrado → lot.write(vals) + audit lot_update (3707-3724)
      └─ si no → try create con savepoint (3753-3754)
                  except IntegrityError/ValidationError:
                     flush_model + invalidate_model (3764-3765)
                     re-search (3766-3771)
                     si lot → lot.write(vals) + audit lot_update (3772-3776)
                     si no → raise
```

**Respuestas puntuales:**
- **Clase/método:** `MadenatGuiaProcessing._create_or_get_lot` (`madenat_guia_processing.py:3570`).
- **Clave efectiva de búsqueda:** `(name, product_id, company_id ∈ [company, False])`, con filtro adicional `reception_id = False`.
- **Protección de recepción:** el filtro `('reception_id', '=', False)` garantiza que un lote nacido en recepción directa **nunca** se reutilice ni sobrescriba desde Procesados.
- **Manejo de colisión:** `try: with cr.savepoint(): stock.lot.create(vals)` / `except (IntegrityError, ValidationError): flush + invalidate + re-search + lot.write(vals)` (`madenat_guia_processing.py:3753-3776`).
- **Al encontrar lote compatible:** lo **reutiliza actualizándolo** (`lot.write(vals)`), no lo rechaza.
- **Campos mutables/inmutables:** mutables = dimensiones, volúmenes, visuales, estados, `guia_processing_id`, OC, proveedor; inmutables = `name`, `product_id`, `company_id` (clave).
- **Exclusividad de origen:** al asignar `guia_processing_id` fuerza `vals['reception_id'] = False` (`madenat_guia_processing.py:3718-3719`).
- **Auditoría:** `_register_lot_audit('lot_creation'|'lot_update', name, ...)` (`madenat_guia_processing.py:3561`), escribe `madenat.audit.log` con `guia_processing_id`, `action_type`, `batch_id=lot_name`, `user_id`.
- **Conexión stock:** `do_full_processing` (946) alimenta `_create_or_get_lot`, y la generación de picking/`stock.move`/`stock.move.line` ocurre aguas abajo (`_create_picking_and_lines`, 3795).

**Tests existentes (solo lectura, no ejecutados):**
- `TestCreateOrGetLotReceptionProtection` — `test_guia_processing.py:255`.
- `test_reception_lot_never_reused` (293): lote con `reception_id` no se reutiliza; ante coincidencia de nombre cae a `create` y choca con la `UNIQUE` nativa (fail-safe).
- `test_lot_without_reception_reused` (335): lote sin `reception_id` se reutiliza (idempotencia preservada).
- `test_lot_creation_emits_audit_event` (555) y `test_lot_reuse_emits_single_lot_update` (581): auditoría de creación/reuso.

---

## 6. Flujo actual de Recepción (Gate 3)

**Cadena completa (hecho confirmado):**

```
action_confirm_reception (lumber_reception.py:2741)
  ├─ validar state='verified' y líneas (2751-2754)
  ├─ guardia anti-duplicado: search_count reception_id (2759-2774)
  ├─ Gate GB-1: nominales completos (2776-2805)
  ├─ auditoría GB-1 superado (2800-2805)
  ├─ auto-reparación de producto (2827-2836)
  └─ try: with cr.savepoint():
        _create_lots_from_packing({})            (2842)
           → LumberReceptionService.create_lots_from_staging(self)  (2017-2018)
        created_lots = search reception_id        (2844)
        picking = service.create_stock_picking(self)  (2850)
        write state='done', lot_ids, picking_id    (2853-2857)
     except Exception → UserError("🛑 Error en el motor de inventario") (2876-2878)
```

**`LumberReceptionService.create_lots_from_staging`** (`reception_service.py:17-102`):

```
existing_lots = search reception_id=reception.id        (31-33)
existing_index = {(name, product_id): lot}             (35-38)   ← se llena UNA vez
for line in reception.reception_line_ids:              (40)
   lookup_key = (lot_name, product_id)                 (43)
   existing = existing_index.get(lookup_key)           (76)
   if existing: existing.write(lot_vals)               (78-86)
   else: stock.lot.create(lot_vals)                    (87-95)  ← NO actualiza existing_index
```

**Por qué falla el caso 15183 (hecho):**
- Primera línea (4809): `existing_index` vacío → `create` (crea `stock.lot` `0000000000446`/166).
- Segunda línea (4810): misma clave `('0000000000446', 166)` → `existing_index` **sigue vacío** (nunca se actualizó) → vuelve a `create` → `UNIQUE(product_id, name, company_id)` → `IntegrityError`.

**`create_stock_picking`** (`reception_service.py:104-165`): crea **un** `stock.move` y **una** `stock.move.line` **por lote** (`for lot in reception.lot_ids`), con `quantity = lot.volume_purchase_m3`. Es decir, **no** genera una línea de movimiento por fila de staging; colapsa el detalle a nivel de lote.

---

## 7. Comparación arquitectónica (Procesados vs Recepción)

| Dimensión | Procesados (`_create_or_get_lot`) | Recepción (`create_lots_from_staging`) |
|---|---|---|
| Búsqueda previa | `flush_model` + `search` (3614-3621) | `search` precargado + índice local (31-38) |
| Clave de búsqueda | `name` + `product_id` + `company` + `reception_id=False` | `(name, product_id)` dentro de la propia recepción |
| Protección entre orígenes | `reception_id=False` excluye lotes de recepción | alcance por `reception_id=reception.id` |
| Colisión concurrente / intra-tx | `savepoint` + `flush` + `invalidate` + re-search + `write` (3753-3776) | **ausente** |
| Reutilización | `lot.write(vals)` (actualiza) | `existing.write(lot_vals)` (78-86) |
| Actualización del índice tras crear | — (re-busca por ORM) | **no actualiza `existing_index` tras create** (bug) |
| Auditoría por lote | `lot_creation` / `lot_update` (`_register_lot_audit` 3561) | no audita creación/reuso por lote (solo GB-1) |
| Detalle por fila | `stock.move.line` por item (aguas abajo) | `stock.move.line` por **lote** (una sola) |

**Reutilizable conceptualmente:** la tríada *búsqueda previa + `savepoint` + re-búsqueda/reutilización* y la auditoría por lote.

**No copiar ciegamente:** el filtro `reception_id=False` y la exclusividad `guia_processing_id`↔`reception_id` (específicos de Procesados). En Recepción el discriminador canónico es `reception_id = self.id`.

---

## 8. Análisis del modelo de datos

| Modelo | Qué almacena | Relevancia para el caso |
|---|---|---|
| `lumber.reception.line` (staging) | `lot_name`, producto, subproducto, espesor/ancho/largo (físico + nominal + documental), piezas, volúmenes, largo/uom | **Único lugar con el detalle completo** (2 filas: 240×4,05 y 50×3,70) |
| `stock.lot` | `name`, `product_id`, `company_id`, `reception_id`, `guia_processing_id`, `espesor_mm`, `ancho_mm`, `largo_m`, `piezas`, volúmenes (un solo valor por dimensión) | **No puede representar dos largos/piezas distintos por lote** sin pérdida |
| `stock.move` / `stock.move.line` | movimiento + línea con `lot_id`, `quantity` (cantidad en la UoM del producto) | Hoy se crea **una** línea por lote (cantidad = volumen del lote) |
| `madenat.audit.log` | `reception_id` / `guia_processing_id`, `action_type`, `batch_id`, `description`, `user_id` | Soporta registrar `lot_creation`/`lot_update`/`omission` |

**Conclusión del modelo:** `stock.lot` almacena **una** tupla dimensional por lote (`espesor_mm`, `ancho_mm`, `largo_m`, `piezas`). Un lote con composición múltiple (dos largos) **no cabe** en `stock.lot` sin elegir un valor y perder el otro. El detalle por fila **sí** puede preservarse en `stock.move.line` (que admite múltiples líneas por `lot_id` y no impone unicidad sobre `lot_id`), o en el staging + auditoría. **No se requiere evolución de modelo** para preservar las dos medidas; se requiere **cambiar el flujo** para emitir una `stock.move.line` por fila de staging (y no una por lote).

---

## 9. Alternativas evaluadas

**Matriz comparativa** (puntaje orientativo: ++/+/0/-):

| Criterio | Alt.1 Validación temprana | Alt.2 Idempotencia intra-recepción | Alt.3 Agrupación previa | Alt.4 Evolución de modelo |
|---|---|---|---|---|
| Fidelidad al documento | - (bloquea lote legítimo multi-fila) | 0 (no preserva 2 largos) | ++ (una fila de move.line por staging) | ++ (modelo dedicado) |
| Trazabilidad física/lote | + | + | ++ | ++ |
| Integridad stock/quants/moves | + | + | ++ | ++ |
| Costos/reportes/exportación | 0 | 0 | + | + |
| Compatibilidad Procesados / exclusividad | + | + | + | + |
| Alcance y riesgo de regresión | bajo | medio | medio | alto |
| Complejidad de pruebas | baja | media | media | alta |
| Adecuación arquitectura MADENAT | parcial | alta | **alta** | media |

- **Alt.1** resuelve el crash pero **rechaza** el caso legítimo (contradice "no asumir que el packing está equivocado"). Insuficiente sola.
- **Alt.2** resuelve el crash (create-or-get intra-recepción) pero **no preserva la composición** de dos largos.
- **Alt.3** resuelve ambos: agrupa por clave `(name, product_id)`, valida compatibilidad (espesor/ancho/subproducto deben coincidir; largo/piezas pueden diferir), crea **un** lote por grupo y **una** `stock.move.line` por fila.
- **Alt.4** es la solución "ideal" a largo plazo si un lote físico debe representar composiciones múltiples como entidad de primer orden, pero es la de mayor riesgo y no es estrictamente necesaria porque `stock.move.line` ya conserva el detalle.

---

## 10. Recomendación técnica

**Alternativa priorizada: Alt.3 (agrupación previa con validación de compatibilidad) + idempotencia intra-recepción (create-or-get, inspirado en `_create_or_get_lot`).**

**Por qué:** resuelve el crash (raíz: índice local no actualizado + ausencia de manejo de colisión) y, a la vez, preserva la composición documental (240×4,05 m + 50×3,70 m) sin inventar sufijos ni consolidar dimensiones.

**Invariantes obligatorias:**
1. **Unicidad estándar intacta** — no se toca la `UNIQUE(product_id, name, company_id)` de Odoo ni `stock.lot.create()` global.
2. **Origen exclusivo** — `stock.lot.reception_id` es la FK canónica; nunca `guia_processing_id` en recepción directa, y viceversa.
3. **No reutilizar lotes de otra recepción** — la búsqueda se acota a `reception_id = self.id`.
4. **No reutilizar lotes de Procesados** — implícito por el alcance `reception_id`.
5. **Escritura de stock solo en Gate 3** — el cambio vive dentro de `create_lots_from_staging`/`create_stock_picking`.
6. **Idempotencia ante reintento** — mismo Gate 3 re-ejecutado no duplica lotes (re-búsqueda por `reception_id`).
7. **Colisión concurrente segura** — `savepoint` + `flush` + `invalidate` + re-search + `write`, como Procesados.

**Clave de identidad propuesta (recepción):** `(name, product_id)` dentro del alcance `reception_id = self.id`.

**Control de compatibilidad dentro del grupo:** si dos filas comparten `(name, product_id)` pero difieren en atributos **de nivel de lote** (espesor, ancho, subproducto), se rechaza con `UserError` claro detallando las líneas y campos en conflicto (no se crea lote ambiguo). Si solo difieren en `largo`/`piezas`/volumen (composición dimensional), se **permite** y cada fila se preserva como una `stock.move.line` distinta.

---

## 11. Pseudocódigo de alto nivel (NO es implementación existente)

```text
# En LumberReceptionService.create_lots_from_staging
grupo = {}   # clave (name, product_id) -> {'lot': stock.lot, 'lineas': [staging]}
for line in reception.reception_line_ids:
    clave = (line.lot_name, line.product_id.id)
    grupo.setdefault(clave, {'compat': {...espesor/ancho/subproducto...}, 'lineas': []})
    if hay_conflicto_de_atributos_de_nivel_lote(grupo[clave], line):
        raise UserError("Lote X incompatible: ... línea A vs línea B ...")
    grupo[clave]['lineas'].append(line)

for clave, g in grupo.items():
    lot = _crear_o_reutilizar_lote(reception, clave, g)   # create-or-get con savepoint
    _registrar_auditoria_lote(lot, 'lot_creation' | 'lot_update')

# En create_stock_picking
for linea in reception.reception_line_ids:      # una move.line por FILA de staging
    lot = mapa_lote[(linea.lot_name, linea.product_id.id)]
    crear stock.move.line(lot_id=lot.id, quantity=linea.vol_purchase_m3)
```

**`_crear_o_reutilizar_lote` (create-or-get, adaptado de `_create_or_get_lot`):**
1. `flush_model` + `search([('reception_id','=',reception.id), ('name','=',name), ('product_id','=',pid)])`.
2. Si existe → `write(vals)` (reutilizar) + auditoría `lot_update`.
3. Si no → `try: with savepoint(): create(vals)` + auditoría `lot_creation`.
4. `except IntegrityError/ValidationError`: `flush` + `invalidate` + re-search (mismo alcance `reception_id`) → si aparece, `write` + auditoría `lot_update`; si no, re-lanzar.

---

## 12. Plan de implementación por fases (no ejecutar sin aprobación)

- **Fase 1 (bug mínimo):** corregir `create_lots_from_staging` para que actualice el índice tras cada `create` (o, mejor, delegar en re-búsqueda ORM con `savepoint`). Añadir manejo `IntegrityError` como Procesados. Archivo: `reception_service.py`.
- **Fase 2 (preservación de composición):** agrupar staging por `(name, product_id)` + validación de compatibilidad de atributos de nivel de lote; emitir una `stock.move.line` por fila de staging en `create_stock_picking`.
- **Fase 3 (auditoría):** registrar `lot_creation`/`lot_update`/`omission` por lote en `madenat.audit.log` con `reception_id`.
- **Fase 4 (pruebas de regresión):** caso 15183 sintético (dos filas, mismo lote, distinto largo/piezas), caso incompatible (mismo lote, distinto ancho), idempotencia (reproceso sin duplicar), protección entre orígenes (un lote de recepción no reutilizado por Procesados y viceversa).
- **Rollback:** los cambios están acotados a `reception_service.py` (y eventualmente `lumber_reception.py` para auditoría); revertir el diff restaura el comportamiento previo.
- **Criterios de aceptación:** el caso 15183 confirma sin error y genera 1 lote + 2 `stock.move.line` (3,596 m³ y 0,685 m³); no se duplica el lote; la auditoría registra `lot_creation`/`lot_update`.

---

## 13. Riesgos y preguntas de negocio pendientes

- **Semántica física de lote/tarja (NO resuelta):** ¿el `lot_name` repetido con distinto largo es UNA tarja con dos medidas, o DOS tarjas que comparten código? La evidencia dimensional (mismo espesor/ancho/subproducto, solo largo/piezas distintos) apunta a la primera, pero **requiere confirmación de negocio** antes de fijar la regla de compatibilidad.
- **Valor de `stock.lot.largo_m` y `stock.lot.piezas`** para un lote multi-fila: el modelo guarda un solo valor por lote; decidir si se almacena la fila dominante (mayor volumen), un consolidado (piezas totales) o si el campo queda informativo y la verdad de detalle vive en `stock.move.line`/staging.
- **`length_nominal = 0.0`** en ambas líneas (observado): no es causa del error, pero conviene validar si el nominal de largo debe fijarse en GB-1 como el espesor/ancho.
- **Auditoría de recepción incompleta** (solo 1 evento `creation`, sin `lot_creation`/`lot_update`): la Fase 3 la cierra.

---

## 14. Anexo de evidencia (comandos de solo lectura)

```bash
docker compose ps
docker compose exec web sh -c 'ps auxww | grep -E "[o]doo|[p]ython"'
docker compose exec web sh -c 'grep -E "^(db_name|db_host|db_port|db_user)" /etc/odoo/odoo.conf'
docker compose exec db psql -U odoo -d madenat_test -c "SELECT current_database(), current_user;"
git status --short && git branch --show-current && git log --oneline -5 && git diff --stat
grep -RInE 'def (create_or_get_lot|create_lots_from_packing|action_confirm_reception|action_validate|do_full_processing)' madenat_lumber_core/models
docker compose exec -T web odoo shell -c /etc/odoo/odoo.conf -d madenat_test --no-http <<'PY'
# consultas ORM read-only (browse/read/search/search_count) del caso 15183
PY
```

**Extractos de código citados (archivo:línea):**
- `madenat_guia_processing.py:3570` `_create_or_get_lot`; `:3616-3621` búsqueda; `:3753-3776` savepoint/IntegrityError; `:3561` `_register_lot_audit`; `:3718-3719` exclusividad.
- `reception_service.py:17` `create_lots_from_staging`; `:31-38` índice local; `:76-95` create/update; `:104-165` `create_stock_picking`.
- `lumber_reception.py:2741` `action_confirm_reception`; `:2842` llamada a `_create_lots_from_packing`; `:2010` `_create_lots_from_packing`; `:2876-2878` envoltorio de error.
- `stock_lot.py:43` `_inherit='stock.lot'`; `:48-55` `_sql_constraints` (solo CHECK, no redefine UNIQUE); `:200` `reception_id`; `:207` `guia_processing_id`; `:378/386/394/402` dimensiones y piezas.
- `test_guia_processing.py:255` protección de recepción; `:293`/`:335` no-reuso/reuso; `:555`/`:581` auditoría.

---

## Conclusión

```text
INVESTIGACIÓN COMPLETADA.
NO SE MODIFICÓ CÓDIGO, DATOS, CONFIGURACIÓN, MÓDULOS NI ESTADO DE INVENTARIO.
PATRÓN DE PROCESADOS ANALIZADO: SÍ.
RUTA DE RECEPCIÓN ANALIZADA: SÍ.
RECOMENDACIÓN: agrupación previa + idempotencia intra-recepción (create-or-get con savepoint) preservando una stock.move.line por fila de staging.
IMPLEMENTACIÓN: PENDIENTE DE APROBACIÓN EXPLÍCITA.
```
