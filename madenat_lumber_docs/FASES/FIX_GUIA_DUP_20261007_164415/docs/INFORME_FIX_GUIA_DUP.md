# INFORME — Validación efectiva de guías duplicadas en la ingesta

**MADENAT — Odoo 18 CE** · 2026-10-07 · **Entrega aislada. NO desplegada.**
Base de la auditoría: `FASES/AUDIT_GUIA_DUPLICADOS_20261007/INFORME_VALIDACION_GUIA_INGESTA.md`.

---

## 1. Qué brecha se corrigió

Las rutas de **Procesado**, **Volúmenes** y el **formulario directo** de `madenat.guia.processing`
fijaban el `name` (número de guía) vía `write()` **sin ejecutar el validador** de duplicados
compartido (`madenat.reception.parser._check_guide_duplicate`, C1). Sólo contaban con el
constraint SQL `UNIQUE(name, partner_id)` (C4), que:

- **no colisiona** cuando `partner_id` es **NULL** → dos cabeceras idénticas por número,
  proveedor nulo (verificado: en el control negativo ese caso **no se detecta**); y
- al no existir el control de aplicación, un duplicado producía un **`IntegrityError`** crudo
  (500) en lugar de un mensaje operativo.

Además, C1 tenía un defecto de exclusión: `exclude_id` se aplicaba **sólo** a la búsqueda en
`lumber.reception`, de modo que reutilizar C1 desde la guía podía **ocultar** una recepción
con el mismo id numérico. Corregido por alcance de modelo.

## 2. Dónde quedó la validación

| Archivo | Cambio |
|---|---|
| `madenat_lumber_core/models/madenat_guia_processing.py` | `create()`/`write()` invocan `_check_guide_identity_duplicate()` (nuevo helper) que **reutiliza C1** con `exclude_model='madenat.guia.processing'`, `cross_model=False`. No duplica la lógica del validador. |
| `madenat_lumber_core/models/reception_parser.py` | C1 acepta `exclude_model` y `cross_model`. La exclusión se aplica **sólo** al modelo indicado. Compatible con el llamador actual (por defecto `exclude_model='lumber.reception'`, `cross_model=True` → comportamiento idéntico al histórico). |
| `madenat_lumber_core/tests/test_guide_duplicate_ingest.py` (+ `tests/__init__.py`) | Suite nueva (26 casos). |

**Orden seguro:** la validación corre **antes** de `super().create()` / `super().write()`, por lo
que **no** se crea cabecera duplicada ni parcial. En las rutas del asistente
(`_route_procesado`, `_route_granel`) el `create + write` están dentro de un
`with self.env.cr.savepoint()`, de modo que el `UserError` **revierte** toda la operación.

## 3. Cómo distingue duplicado, homónimo e identidad incompleta

Ver `MATRIZ_IDENTIDAD.md`. En síntesis:

- **Duplicado (A):** misma clave natural `name` + `partner` (igual, o ambos nulos) en el **mismo**
  modelo → bloquea con el mensaje de C1.
- **Homónimo (B):** número coincidente **sólo en el otro modelo** (recepción ↔ guía), o `partner`
  conocido y **distinto** → **no** bloquea (el número no es clave global, CANON/12 §5.2).
- **Incompleto (C):** número con **un** lado de `partner` desconocido → **bloquea** (postura
  conservadora; **decisión revisable**, ver riesgos).
- **Propio (D/E):** exclusión por **modelo+id** → nunca duplicado de sí mismo; relectura idempotente.

## 4. Rutas y efectos probados

- **Procesado** (`action_verify_data` → `write`), **Volúmenes** (`_route_granel` → `write`) y
  **formulario directo** (extracción al subir Excel / tecleo) → cubiertos por el `write`.
- **Recepción/Producto** (llamador existente, C2) → regresión verificada.
- **Efectos**: sólo se verificó la **cabecera** y sus líneas de staging (el bloqueo ocurre antes
  de materializar lotes/stock). **No** se probó no-duplicación de lotes/movimientos.

## 5. Impacto en llamadores existentes

- `reception_workflow.py:107` (`_check_guide_duplicate(..., exclude_id=reception.id)`): **sin
  cambios**; usa los valores por defecto → comportamiento idéntico (recepción excluida, guía
  homónima **no** excluida, ambos modelos inspeccionados).
- `test_duplicate_validation.py` (8 tests): **0 fallos** tras el cambio.
- Ningún otro llamador de C1 existe (verificado por búsqueda).

## 6. Límites de seguridad y concurrencia

- El control corre con el **usuario operativo real** (el guard `_require_intake_operational_group`
  ya exige rol); C1 usa `sudo()` **interno pre-existente** — **no** se agregó `sudo` nuevo. La
  búsqueda está filtrada por compañía/proveedor cuando aplica; la guía **no** tiene `company_id`.
- **Concurrencia:** el `search` previo protege el caso **secuencial**. **NO** se declara blindaje
  concurrente: *search-then-insert* tiene carrera. El backstop concurrente es `UNIQUE(name, partner_id)`
  — que **no** cubre el caso `partner_id` nulo. Ver riesgos.
- **«Advertir sin bloquear» (caso B):** **no** se emite una advertencia no bloqueante. Desde
  `create()`/`write()` el único mecanismo existente y comprobado es el `UserError` de C1, que
  **bloquea**; los llamadores del asistente (`_route_procesado`, `_route_granel`) sólo capturan
  excepciones (`UserError`/`ValidationError`) y en ese caso ponen `state='error'`. Por tanto **no**
  se afirma que un «warning» retornado desde `create/write` sea visible. El caso B se resuelve
  **permitiendo** la operación (sin advertencia); añadir una advertencia no bloqueante requeriría
  el menor ajuste UX en el asistente (fuera del alcance mínimo y no implementado).


## 7. Riesgos abiertos y decisiones pendientes

1. **Caso C (revisable):** con `partner` nulo en un lado se **bloquea** por número. Es conservador;
   si la doctrina prefiere advertir sin bloquear, es un cambio puntual acotado.
2. **Carrera concurrente con `partner_id` nulo:** persiste (el SQL no la cubre). Propuesta mínima
   **separada** (p. ej. índice único parcial / centinela gestionado). **No** implementada aquí.
3. **Formulario directo:** si el bloqueo ocurre sobre un borrador ya abierto por el usuario, éste
   conserva su borrador con el nombre previo (`'New'`); no se creó nada, pero el registro de
   borrador continúa existiendo (comportamiento del usuario, no del control).
4. **Caso C en flujos automáticos:** en `action_verify_data` y `_route_granel` el `name` y el
   `partner` se escriben **juntos**, por lo que C casi no ocurre; en «formulario directo» con sólo
   número sí puede aparecer.
5. La ruta de **Recepción** sigue inspeccionando ambos modelos (`cross_model=True`), por lo que un
   número homónimo en guía podría bloquear una recepción. **No** se cambió (fuera del alcance y con
   regresión protegida); se anota como **asimetría a revisar** en una intervención aparte.

## 8. Autorización que falta para aplicar

- **No** se aplicó al árbol activo ni a `madenat_test`. Para desplegar se requiere autorización
  explícita para: (a) aplicar el parche a `custom_addons/`; (b) `-u madenat_lumber_core` en
  `madenat_test` en ventana operativa; (c) reiniciar `odoo18_app`. **No** se ejecuta aquí.

---

## CIERRE EXIGIDO

1. **Brecha corregida:** Procesado/Volúmenes/formulario directo no validaban duplicados al fijar
   el número; sólo el SQL, ciego ante `partner_id` nulo y no amable. Además, la exclusión de C1 no
   estaba acotada por modelo.
2. **Dónde quedó:** en `create()`/`write()` de `madenat.guia.processing`, **antes** de persistir,
   reutilizando C1 (C1 extendido con `exclude_model`/`cross_model`).
3. **Distingue:** por la **clave natural** `name`+`partner` y el **modelo**; homónimo entre modelos
   o proveedor distinto → no bloquea; incompleto → bloqueo conservador (revisable); propio → excluido
   por modelo+id.
4. **Rutas/efectos probados:** Procesado, Volúmenes, formulario directo, Recepción (regresión);
   efecto verificado = cabecera+líneas de staging (no lotes/movimientos).
5. **Riesgos abiertos:** caso C (revisable), carrera concurrente con partner nulo, asimetría del
   camino Recepción, borrador del formulario directo.
6. **Autorización faltante:** aplicar al árbol activo + `-u` + reinicio (ver §8).

**No desplegado. No se modificaron datos históricos. Hay rutas documentadas como fuera de cobertura
(concurrencia real y no-duplicación de lotes).**

