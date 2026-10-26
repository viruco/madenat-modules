# PLAN DE APLICACIÓN — corrección de identidad cross-model (guía 15183)

> **Estado: NO aplicado.** Este plan se ejecuta **sólo con aprobación explícita**.
> No modifica datos ni la guía 33154. No reingresa documentos.

## A. Archivos y orden

| # | Archivo (`madenat_lumber_core/…`) | Cambio | Tipo |
|---|---|---|---|
| 1 | `models/reception_parser.py` | `_check_guide_duplicate`: identidad (emisor) + guard de identidad incompleta en ámbito cruzado | código |
| 2 | `models/madenat_guia_processing.py` | `cross_model=True` en los 2 llamadores de bloqueo | código |
| 3 | `models/reception_workflow.py` | `_check_duplicate_and_warn`: `cross_model=True` + `partner_id` | código |
| 4 | `tests/test_guide_duplicate_ingest.py` | `test_03`, `test_28`, `test_08b`, `test_29` corregidas | pruebas |
| 5 | `tests/test_guide_duplicate_warnings.py` | `w2`, `w5`, `w8` corregidas | pruebas |
| 6 | `tests/__init__.py` + `tests/test_guide_dup_regression_15183.py` | nueva suite de regresión | pruebas |

Parche exacto: `DIFF_MINIMO.patch` (269 líneas). Sólo `models/` y `tests/` — sin
tocar CANON, ACL, `security/*.csv`, XML, esquema ni índices.

## B. Procedimiento

1. **Gate previo:** `diff` workcopy vs artefacto probado → byte-idénticos; suite
   aislada `0 failed, 0 error(s)` (ya verificado).
2. **Respaldo:** código (`custom_addons` limpio) + `pg_dump -Fc madenat_test` +
   filestore. Destino `backups/INCIDENTE_GUIA_15183_<ts>/`.
3. **Ventana:** detener `odoo18_app`.
4. **Aplicar** el parche mínimo al árbol activo `custom_addons/`.
5. **Actualizar** one-shot: `odoo -u madenat_lumber_core --no-http
   --max-cron-threads=0 --workers=0 --stop-after-init` sobre `madenat_test`.
6. **Reiniciar** `odoo18_app`; verificar `GET /web/login` HTTP 200 y log sin
   `ERROR/CRITICAL`.
7. **Prueba funcional (sin ingesta real):** sobre una base **aislada** (no
   `madenat_test`), verificar los dos órdenes; **no** reingresar 15183.

## C. Verificación (criterios de aceptación)

- Crear un Procesado con el mismo **número+emisor** de una Recepción existente →
  **bloquea** con el mensaje de C1 (N°, proveedor, fecha, estado, ID).
- Emisor **distinto** con el mismo número → **no** bloquea (sigue permitido).
- Captura incompleta (emisor desconocido) → **no** bloquea; al completar identidad
  con la del documento existente → **bloquea**; con emisor distinto → **no**.
- Relectura del propio documento → idempotente (sin bloqueo falso).
- Homónimo → sigue el **aviso** no bloqueante en el chatter.
- `TestGuideDuplicate*` y `TestDuplicateValidation` en verde.

## D. Decisiones pendientes (separadas, no incluidas)

1. **Identidad por RUT (residual):** existe ≥1 caso de **dos `res.partner` con el
   mismo RUT** (`77066489-6` → `664`, `676`). Comparar por `partner_id` **no** los
   unifica. Propuesta opcional (requiere ratificación): aceptar coincidencia por
   `vat` normalizado como refuerzo. **No** implementado.
2. **Momento de la comprobación en la ruta de Recepción:** el pipeline valida en
   el paso 2.5, **antes** de resolver el proveedor (paso 6). Con
   `partner_id=reception.supplier_id.id or None`, la confirmación cruzada
   Recepción→Guía ocurre cuando el proveedor ya está poblado (p. ej. reproceso).
   Opción (requiere decisión): resolver el emisor desde `dg_data['supplier_rut']`
   en el punto de validación. **No** implementado (evita una regla nueva).
3. **Concurrencia real:** no cubierta (el `search` previo es secuencial).

## E. Reversión

Restaurar los 3 archivos de `models/` y los 3 de `tests/` desde el respaldo y
`-u madenat_lumber_core`. Sin cambios de esquema → reversión limpia.

## F. Límites

- **No** se toca ni reprocesa la guía **33154** ni ningún registro real.
- **No** se despliega a producción ni se hace commit/push desde esta entrega.
