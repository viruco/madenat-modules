# CHECKLIST MANUAL (NAVEGADOR) — FASE 10 · Mauricio

**Objetivo:** confirmar en pantalla, con el módulo actualizado (`madenat_lumber_logistics` **18.0.1.32.0**), los
tres criterios de cierre del flujo **«Rebaja de etiquetas»**. Sin tocar datos reales de producción: usar la
**base de desarrollo/prueba** que indique el equipo.

**Antes de empezar:** anotar (o hacer captura de) el estado de partida del SV `SV00000000841` y de los documentos
`IMP02220` (aplicada) e `IMP04823` (anulada). **No** se debe modificar el SV ni esos dos documentos durante la
revisión; si alguna prueba crea un borrador, **anularlo al terminar** (no aplicarlo).

---

## Checklist

| # | Qué hacer en pantalla | Qué debe pasar | ✔ | Notas |
|---|---|---|---|---|
| 1 | Logística → **Rebaja de etiquetas** → abrir `SV00000000841` (o el SV que tenga documentos anulados) | La sección **«Trabajo en preparación (no aplicado)»** **NO** muestra `IMP04823` (anulada) | ☐ | |
| 2 | Mirar la columna/servicio **«Trabajo en prep.»** del listado «Etiquetas SV» para ese SV | Muestra **0** (no cuenta la anulada) | ☐ | |
| 3 | Abrir el asistente de rebaja sobre esa etiqueta SV y pulsar **Guardar** **sin** marcar ninguna etiqueta | **Bloquea** con un mensaje en español que pide **seleccionar al menos una etiqueta**; **no** se crea ningún documento | ☐ | |
| 4 | Marcar **1 o 2 etiquetas** (las que correspondan a la rebaja) y pulsar **Guardar** (sin escribir cantidades) | Se crea un documento **nuevo** y **las etiquetas quedan registradas** en él (pestaña de etiquetas con líneas). **No** aparece el error «…ya no admite preparación (estado applied)» | ☐ | Es el caso reportado de la guía **1198** con `IMP02220` aplicada |
| 5 | Pulsar **Guardar** otra vez sin cambiar nada | Reutiliza el **mismo** borrador (no se duplica el documento) | ☐ | |
| 6 | Volver a la ficha del SV | La sección «Trabajo en preparación» muestra **solo** el borrador nuevo (contador **1**); la anulada sigue sin aparecer | ☐ | |
| 7 | Si existe un documento **anulado** de la misma guía y se prepara **la misma** selección | Se crea un documento **nuevo** (clave distinta); el **anulado queda intacto** (mismos estado y clave) | ☐ | |
| 8 | Aplicar una selección (caso normal: seleccionar → escribir m³ → **Aplicar**) y luego intentar preparar **la misma selección** | Mensaje claro: **«ya se aplicó con esta misma selección»**; **no** se duplica ni se altera el aplicado | ☐ | |
| 9 | Sobre un documento **aplicado**, pulsar **Continuar** (si el enlace sigue disponible) | Devuelve un **mensaje operativo** («…no es Trabajo en preparación…»), **no** un error técnico | ☐ | |
| 10 | Anular un borrador y luego **«Volver a borrador»** indicando el motivo | La reapertura sigue funcionando igual que antes (RESET intacto) | ☐ | |
| 11 | Caso sano de punta a punta: seleccionar → indicar m³ → **Aplicar** | Se aplica correctamente: el SV muestra **Rebajado documental** con el volumen indicado y el detalle en «Asignaciones documentales (histórico)» | ☐ | |
| 12 | Verificar que `IMP02220` e `IMP04823` conservan su **estado**, sus **valores** y su **clave documental** | Sin cambios respecto al paso inicial | ☐ | |

---

## Qué reportar si algo no cuadra

Enviar: (a) el paso del checklist, (b) la captura de pantalla, (c) la **referencia** del documento implicado
(`IMP…`) y el **SV** (`SV…`), y (d) la hora aproximada. Con eso se puede cruzar con la bitácora
(`madenat.audit.log`) y los registros de la operación.

**Recordatorio:** esta revisión es **de sólo lectura** salvo los borradores de prueba que se creen (que deben
**anularse**, no aplicarse). No se tocan datos reales de producción ni el SV `SV00000000841` en su estado actual.
