# Avisos no bloqueantes y prevención de repetición

## Mecanismo

El aviso no bloqueante se publica en el **chatter del propio registro** (`message_post`,
`mail.thread`), ya presente tanto en `lumber.reception` como en `madenat.guia.processing`.
El método **`_warn_guide_homonym(name, model_name)`** vive ahora en el **mixin compartido**
`madenat.lumber.ingest.mixin` (lo heredan ambos modelos), por lo que **no** se duplica código
ni se añade modelo, campo, asistente ni subsistema de notificaciones.

- **No expone datos de otro registro:** sólo el N° que el usuario ya conoce y la categoría
  (`Recepción directa` / `Guía Procesada`). No incluye id, proveedor ni enlace del otro documento.
- **No crea documentos:** sólo comenta en el propio registro.
- **La detección efectiva permanece en servidor** (C1). El aviso es UX y no sustituye la validación.

## Puntos de emisión

| Ruta | Dónde | Sentido del aviso |
|---|---|---|
| Procesado / Volúmenes / formulario directo (guía) | `madenat.guia.processing._check_guide_identity_duplicate` (tras la validación confirmada) | Guía ↔ Recepción |
| Recepción (Producto) | `reception_workflow.LumberReceptionWorkflow._check_duplicate_and_warn` (bloque 2.5 del pipeline) | Recepción ↔ Guía |

Ambos sentidos fueron probados (ver `RESULTADOS_PRUEBAS.md` w1–w2). En ningún caso el aviso
bloquea ni crea una cabecera adicional.

## Prevención de avisos repetidos (criterio)

**Criterio: sólo se evalúa/avisa cuando la IDENTIDAD CAMBIA en la operación.**

- **Guía (`write`)**: la identidad es `name` + `partner_id`. Si `vals` no altera ninguno, no se
  revalida ni se reavisa (`if name == rec.name and partner_id == rec.partner_id` → `continue`).
  Modificar un **campo ajeno** a la identidad no dispara nada (el helper sólo corre si `name` o
  `partner_id` están en `vals`).
- **Recepción (pipeline)**: el aviso se emite **sólo** si el número detectado
  (`guide_no_for_check`) **difiere** del almacenado en la cabecera (`reception.name`). Tras la
  primera corrida, `_update_header_data` guarda el número, de modo que una **relectura/reintento**
  con el mismo número no repite el aviso.

El criterio distingue así:

| Situación | Comportamiento |
|---|---|
| Coincidencia ya advertida y **sin cambios** | **No** genera aviso nuevo |
| **Cambio real** de identidad | Revalida y avisa si aplica |
| **Nueva** coincidencia pertinente | Avisa |

**Sin campos persistentes** y **sin** usar texto traducido como clave de deduplicación (el
criterio es funcional: cambio de identidad / cambio de número). No se prueba idempotencia
**concurrente** del aviso; sólo la repetición **secuencial**.

## Atomicidad

El `message_post` ocurre dentro de la **misma transacción** que la operación; si el pipeline
falla después (p. ej. Gate 1), el aviso se **revierte** con el resto (probado en `w8`). No
queda una advertencia que describa un ingreso exitoso inexistente.

## Límite declarado

- La deduplicación del aviso de **Recepción** se apoya en que el número quede almacenado en la
  cabecera (flujo real: el pipeline lo escribe tras el chequeo). Si una recepción se creara
  **ya con el número** y nunca cambiara, el primer chequeo no emitiría aviso (caso menor,
  documentado). **No** se cubre aquí la concurrencia (propuesta separada).
- El aviso es de **chatter** (probado a nivel servidor). **No** se verificó en navegador.
