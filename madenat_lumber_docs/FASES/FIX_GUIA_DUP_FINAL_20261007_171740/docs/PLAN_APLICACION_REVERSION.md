# Plan exacto de aplicación y reversión (NO ejecutado)

## A. Archivos y diffs exactos (todo en `madenat_lumber_core`)

**Diff incremental vs parche CIERRE** (`patch/incremental/`):
| Archivo | Cambio | Diff |
|---|---|---|
| `models/mixin_lumber_ingest.py` | +`_warn_guide_homonym` (mixin compartido) | 34 líneas |
| `models/madenat_guia_processing.py` | gate «identidad sin cambios ⇒ sin aviso»; retira aviso local | 39 líneas |
| `models/reception_workflow.py` | `_check_duplicate_and_warn` + args explícitos | 68 líneas |
| `tests/test_guide_duplicate_warnings.py` | **nuevo** (10 tests) | 183 líneas |
| `tests/__init__.py` | registra la suite nueva | 10 líneas |

**Diff consolidado vs árbol activo** (`patch/consolidado/`): incluye el parche previo + este
cierre (reception_parser 255, madenat_guia_processing 131, mixin 34, reception_workflow 68,
tests). **Sin cambios de esquema, campos, ACL ni constraints.**

Separación de tamaño: **código productivo** ≈ mixin(34)+guia(39)+workflow(68) = **141 líneas**;
**pruebas/documentación** ≈ 183+10 = **193 líneas**.

## B. Orden de aplicación

1. **Respaldo (obligatorio antes de tocar):**
   - Código con cambios locales: `tar` de los **5 archivos** destino (o del árbol `custom_addons`
     completo) con su estado actual.
   - Base: `pg_dump` de `madenat_test` (como en `backups/…`).
   - Filestore: tar de `/var/lib/odoo/filestore/madenat_test` (volumen `odoo-18-ce_odoo-web-data`).
2. Detener `odoo18_app` (o ventana operativa con `--max-cron-threads=0`).
3. Aplicar el diff **consolidado** (o el incremental si se parte del workcopy CIERRE) con `patch`,
   desde `custom_addons/madenat_lumber_core/` (ajustar `-p` al prefijo del diff).
4. `-u madenat_lumber_core` en `madenat_test` (contenedor one-shot
   `--no-http --max-cron-threads=0 --workers=0 --stop-after-init`).
5. Reiniciar `odoo18_app`.
6. Validaciones posteriores (ver E).

## C. Módulos realmente afectados

Determinado por los archivos efectivamente modificados: **sólo `madenat_lumber_core`**.
Ningún otro módulo cambia archivos. Los módulos dependientes (`madenat_lumber_intake`,
`madenat_lumber_logistics`, `madenat_lumber_costing`, `madenat_toll_processing`,
`madenat_vendor_payment`, `madenat_lumber_reception_improvements`) **se recargan
transitivamente** con `-u madenat_lumber_core` (Odoo actualiza los dependientes), por lo que
**no** se requiere `-u` explícito de cada uno; se recomienda revisar el log por errores.

## D. Base y servicio destino propuestos

- Base: **`madenat_test`** (la del servicio activo). **No** producción.
- Servicio: `odoo18_app` (reinicio controlado); contenedor one-shot para el `-u`.
- **NO** se toca el árbol activo durante las pruebas (ya probado en `dupval3_*`).

## E. Validaciones posteriores

1. Suite en la base destino: `TestGuideDuplicateWarnings` + `TestGuideDuplicateIngest` +
   `TestDuplicateValidation` → esperado **`0 failed`**.
2. Conteo de duplicados: `search_count` de cabeceras = 1 por identidad en los casos probados.
3. Log de `-u`: 0 `ERROR`/`CRITICAL`/`Traceback`.
4. `GET /web/login` → HTTP 200; servicio `Up`.
5. Comprobación funcional mínima: subir una guía homónima → aparece **aviso** (no bloqueo) en el
   chatter; un duplicado confirmado → **bloqueo** con el mensaje de C1.

## F. Reversión

- **Código:** `patch -R` del diff aplicado (orden inverso) o restaurar los 5 archivos desde el
  respaldo; luego `-u madenat_lumber_core` para recargar.
- **Esquema/ACL/datos:** **sin cambios** (no hay campos, constraints ni ACL nuevos) → la
  reversión de código **basta**; no requiere restauración de base.
- **Límite:** si la aplicación quedara parcialmente inconsistente (p. ej. `-u` fallido a medias),
  la vía segura es **restaurar el `pg_dump` + filestore** del respaldo (la reversión de código
  **no** cubre datos si algo se escribió durante la ventana). Por eso el respaldo se toma **antes**.
- Riesgo global: **bajo** (sólo lógica de validación/aviso; no toca stock, valoración,
  contabilidad, ACL ni datos históricos).

## G. Decisiones necesarias antes de producción (separadas)

1. Cierre del residuo `partner_id` nulo (índice único parcial) — **no** incluido.
2. Ratificación AD-88 del aviso pasivo (o exigir motivo).
3. Concurrencia real — propuesta separada.
