# Propuesta — Protección contra SOBRESCRITURA de borradores (conflicto de edición concurrente)

**Fecha:** 2026-10-12 · **Entorno:** `madenat_test` (LOCAL) · **Estado:** **PROPUESTA — NO IMPLEMENTADA**
**Autorización requerida:** **Mauricio** (no se activa ninguna política nueva de conflictos sin su aprobación).
**Alcance:** `madenat.sv.imputation` (documento de rebaja) + asistente `madenat.sv.imputation.wizard`.

> **Regla de esta intervención:** este documento **describe y fundamenta** una propuesta. **No** introduce
> código, no cambia el comportamiento actual («última escritura gana») y deja el riesgo como **PENDIENTE**.

## 1. Riesgo observado (comportamiento actual)
El documento de rebaja y su asistente siguen el patrón ORM estándar: **«la última escritura gana»**. Si dos
sesiones editan el MISMO borrador (p. ej. el mismo `madenat.sv.imputation` en `draft`/`pending`) y una guarda
después de que la otra ya lo hizo, la segunda sobrescribe silenciosamente la primera **sin advertencia**.
Los controles actuales protegen la **capacidad** y la **transición de estado** (advisory locks, revalidación,
techo duro, `_check_single_work_per_guia`), pero **no** detectan una edición obsoleta sobre el mismo
documento ya guardado.

## 2. Propuesta concreta (mínima y compatible con «Guardar»/«Aplicar»)

### 2.1 Identificación de versión del documento
- Añadir al documento `madenat.sv.imputation` un campo de versión lógica, p. ej.
  `edit_version = fields.Integer(default=1, copy=False)` (columna ADITIVA; sin migración de datos).
- `write()` (y las acciones que consolidan cambios: `action_prepare`, `action_apply`) incrementan
  `edit_version` en cada escritura efectiva de contenido (no en escrituras de solo trazabilidad).

### 2.2 Detección de edición obsoleta
- El asistente recibe, al abrirse, la `edit_version` vigente del documento (en su `context`/campo interno).
- Al pulsar **Guardar** o **Aplicar**, el backend compara la versión recibida con la actual:
  - **Igual** ⇒ procede (comportamiento actual).
  - **Distinta** ⇒ **no** escribe; devuelve un aviso controlado (`UserError`/`ValidationError`) indicando que
    el documento cambió en otra sesión.
- Se apoya en el mismo punto único que ya existe (`write()` del documento y `action_*`), **sin** duplicar la
  lógica en la vista.

### 2.3 Mensaje al usuario
Mensaje operativo (no técnico), p. ej.:
> «El documento IMP… fue modificado por otra sesión mientras lo editabas. Tus cambios NO se guardaron para
> no sobrescribir los de la otra sesión. Recarga el documento para ver la versión actual y vuelve a aplicar
> tus cambios.»

### 2.4 Conservación de cambios locales
- Los valores que el operador tenía en pantalla **no** se envían al backend (no hay sobrescritura) y
  permanecen en el formulario del asistente.
- El asistente ofrece **Recargar** (descarta la edición local y trae la versión vigente) o **Reintentar**
  (reenvía comparando con la versión recién leída), según elija el operador.

### 2.5 Reintento o recarga
- **Recargar:** `reload()` del formulario del asistente con `edit_version` renovada.
- **Reintentar:** el operador confirma aplicar sus valores sobre la versión vigente; el backend revalida
  capacidad/conflicto como hoy (idempotencia y locks ya existentes) e incrementa la versión.

### 2.6 Compatibilidad con **Guardar** y **Aplicar**
- **Guardar** y **Aplicar** comparten la MISMA comprobación de versión (un único punto backend).
- El recorrido simple (seleccionar material → indicar m³ → Guardar/Aplicar en la misma ventana) **no cambia**:
  la comprobación solo actúa cuando hay conflicto real.

## 3. Alternativas descartadas
- **Bloqueo pesimista del documento** (impedir abrir el borrador a dos sesiones): degrada la UX y no cubre
  sesiones que quedaron abiertas; se prefiere detección optimista por versión.
- **Recomputar/merge automático**: descartado por riesgo de fusiones incorrectas en repartos documentales.
- **`pg_advisory_lock` durante toda la edición**: descartado (locks de larga duración; el lock actual es de
  **transacción** y solo cubre la aplicación, no la edición humana).

## 4. Impacto si se aprueba
- Cambio **LOCAL** y acotado; columna aditiva; sin tocar stock, ledger ni histórico.
- Requiere pruebas dedicadas (dos sesiones, versión obsoleta, recarga/reintento, compatibilidad Guardar/Aplicar).
- **No** se implementa en esta intervención: queda **PENDIENTE DE APROBACIÓN EXPLÍCITA DE MAURICIO**.
