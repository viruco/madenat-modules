# Matriz de identidad documental y comportamiento (resolución de D1)

**Punto de intervención:** `madenat.guia.processing.create()` / `.write()` (donde **todas** las
rutas de guía —Procesado, Volúmenes y formulario directo— fijan el `name`), reutilizando el
validador existente `madenat.reception.parser._check_guide_duplicate()` (C1).

**Claves naturales reales (no se inventan):**

| Modelo | Clave natural | Constraint SQL vigente |
|---|---|---|
| `lumber.reception` | `name` (+ `company_id`) | `UNIQUE(name)` |
| `madenat.guia.processing` | `name` + `partner_id` | `UNIQUE(name, partner_id)` |

`madenat.guia.processing` **no tiene `company_id`** (verificado en código), por lo que su
clave es `name` + `partner_id` y el validador cae en su rama sin filtro de compañía.

## Matriz de casos (§4)

| Caso | Condición sobre la clave natural | Comportamiento implementado | Justificación |
|---|---|---|---|
| **A** Duplicado confirmado | mismo `name` y partner **igual** (ambos conocidos e iguales, **o ambos vacíos**) | **BLOQUEA** con el mensaje de C1 (muestra N°, proveedor, fecha, estado, id del existente) | la clave `name`+`partner` es la identidad natural; el número sí es clave **dentro** del mismo documento/modelo |
| **B** Mismo número, documento positivamente distinto | mismo `name` con partner **conocido y distinto**; o coincidencia **sólo** en el **otro** modelo (recepción ↔ guía) | **NO bloquea** | la clave natural incluye `partner` (SQL permite proveedores distintos); y el número **no** es clave global (CANON/12 §5.2: `guia_number` es informativo) |
| **C** Identidad insuficiente/contradictoria | mismo `name` con **un** lado con partner desconocido y el otro conocido | **BLOQUEA** (postura conservadora) — **DECISIÓN REVISABLE** | no hay combinación de datos disponibles que pruebe documento distinto; bloqueo conservador consistente con C1. *Pendiente de confirmación doctrinal* |
| **D** Edición del propio registro | el match sería `self` | **NUNCA** es duplicado | exclusión por **modelo+id** (`exclude_model='madenat.guia.processing'`) |
| **E** Relectura / documento complementario | reescritura del mismo registro / re-derivación del wizard | mismo ingreso, sin segunda cabecera | exclusión propia + idempotencia (C7 del wizard) |
| **F** Existente cancelado | existente en `state='cancelled'` | **BLOQUEA** igual que cualquier duplicado | política vigente: no se ignora por estar cancelado |

## Reglas explícitas respetadas

- **No** se usa «distinto modelo» como prueba suficiente de documento distinto → para el caso
  B que se apoya **sólo** en el otro modelo se usa el respaldo doctrinal (número no es clave
  global), no el mero hecho de ser otro modelo.
- **No** se usa «mismo número» como prueba suficiente de duplicado → el número por sí solo no
  bloquea entre modelos ni con proveedor distinto.
- **No** se impone proveedor/fecha/tipo como clave obligatoria sin respaldo: proveedor ya era
  parte de la clave natural (`UNIQUE(name, partner_id)`); **no** se agregó fecha ni tipo.
- Si la doctrina no resuelve (caso C) → se documenta como **decisión pendiente**, sin inventar
  política silenciosa.
