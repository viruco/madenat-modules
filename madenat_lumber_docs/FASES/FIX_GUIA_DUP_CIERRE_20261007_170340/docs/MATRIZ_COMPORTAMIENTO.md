# Matriz de comportamiento (antes → después)

Casos (según §4 del prompt). «Antes» = parche previo (`FIX_GUIA_DUP_20261007_164415`).
«Después» = esta entrega (ajustes A/B/C).

| Caso | Antes (parche previo) | Después (esta entrega) |
|---|---|---|
| **A. Duplicado confirmado** (mismo modelo, `name`+`partner` conocidos e iguales) | Bloquea (UserError) | **Bloquea** (igual) |
| **B. Mismo número, documento distinto** (otro proveedor, o sólo otro modelo) | Guía: no bloquea. Recepción: **bloquea** (asimetría) | **No bloquea** en ninguno de los dos sentidos (simétrico) + **aviso** homónimo |
| **C. Identidad incompleta** (`partner_id` nulo) | **Bloquea** por número (conservador) | **No bloquea**; conserva la captura; **revalida** al completar |
| **D. Edición del propio registro** | No es duplicado de sí mismo | Igual (exclusión por modelo+id) |
| **E. Relectura / archivo complementario** | Idempotente (mismo ingreso) | Igual + aviso si hay homónimo real |
| **F. Documento existente cancelado** | Bloquea (no lo ignora) | Igual (sigue contando) |
| **G. Número vacío / provisional `'New'`** | No valida | Igual (no valida) |
| **H. Escritura de campo ajeno a la identidad** | No revalida | Igual (no revalida) |
| **I. Conflicto intra-lote (mismo lote)** | Detecta (identidad completa o nula) | Detecta con **identidad completa**; incompleto no bloquea (AJUSTE A) |
| **J. Coincidencia cross-model en Recepción** | Bloqueaba (cross_model=True) | **No bloquea** (default `cross_model=False`, simetría) |
| **K. Aviso al usuario (no bloqueante)** | No existía | **Chatter** (`mail.thread`) con el N° y la categoría del documento coincidente |

## Clasificación de identidad (implementada)

- **Identidad completa** = `name` real (≠ `'New'`) **y** `partner_id` conocido.
- **Duplicado confirmado** = misma identidad completa en el **mismo modelo** (guía).
- **Homónimo** = mismo `name` con identidad NO confirmada (otro proveedor u otro modelo).
- **Incompleto** = `name` real pero `partner_id` nulo → no se valida como duplicado.

## Límites (declarados)

- **Residual `partner_id` nulo:** dos cabeceras con el mismo número y ambos proveedores
  nulos **no** colisionan en la SQL `UNIQUE(name, partner_id)` ni se bloquean (AJUSTE A).
  Cerrado sólo al completar el proveedor. Cierre definitivo = propuesta **separada**
  (índice único parcial). Ver `RESULTADOS_PRUEBAS.md` (test_30).
- **Concurrencia real:** el `search` previo protege lo **secuencial**; **no** se declara
  blindaje concurrente.
