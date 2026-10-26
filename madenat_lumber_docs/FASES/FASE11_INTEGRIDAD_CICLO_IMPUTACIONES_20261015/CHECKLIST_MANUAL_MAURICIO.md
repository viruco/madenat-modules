# CHECKLIST MANUAL (NAVEGADOR) — FASE 11 · Mauricio

**Objetivo:** confirmar en pantalla, con el módulo actualizado (`madenat_lumber_logistics` **18.0.1.36.0**), que el
**ciclo de vida de la imputación SV** sólo cambia por sus acciones oficiales y que no se puede alterar después.
**No** tocar datos reales de producción: usar la base de desarrollo/prueba que indique el equipo.

**Antes de empezar:** anotar el estado de partida de `IMP02220` (aplicada) e `IMP04823` (anulada) y de su SV.
Si alguna prueba crea un borrador, **anularlo al terminar** (no aplicarlo).

| # | Qué hacer en pantalla | Qué debe pasar | ✔ | Notas |
|---|---|---|---|---|
| 1 | Logística → **Rebaja de etiquetas** → preparar una guía con 1–2 etiquetas y pulsar **Guardar** | Se crea/reutiliza el **borrador** con sus etiquetas; nada se aplica | ☐ | |
| 2 | Pulsar **Dejar pendiente** y luego **Volver a borrador** | Ambas transiciones funcionan igual que antes | ☐ | |
| 3 | Marcar etiquetas, indicar m³ y pulsar **Aplicar** | Queda **Aplicada**; el SV muestra **Rebajado documental** con el volumen. El documento muestra **Aplicada por** y **Fecha de aplicación** | ☐ | |
| 4 | Abrir ese documento **aplicado** y mirar la pestaña «Motivo / Reversa» | «Motivo de reversa», «Anulada por/fecha», «Reabierta por/fecha» y «Imputación de origen» son de **sólo lectura** | ☐ | |
| 5 | En el aplicado, escribir el **motivo** en el campo «Motivo (anular / reversar / volver a borrador)» y pulsar **Reversar** (Jefatura/Gerencia) | Se reversa; el motivo queda congelado en «Motivo de reversa»; el SV libera el saldo. En el chatter aparece la nota | ☐ | Operaciones **no** puede reversar |
| 6 | Intentar **Anular** un borrador **sin** escribir el motivo | **Bloqueado**: «Indique el motivo de la anulación antes de anular…» | ☐ | |
| 7 | Escribir el motivo y pulsar **Anular** | Se anula; el motivo queda en «Motivo de anulación» y en el **chatter** | ☐ | |
| 8 | Con el documento **anulado**, abrir la pestaña «Etiquetas» e intentar añadir o quitar una línea (y un reparto) | **Bloqueado** con mensaje de negocio (contenido inmutable) | ☐ | Desde la lista editable: el error sale al guardar |
| 9 | Con el documento **anulado**, pulsar **Volver a borrador** indicando el motivo | Se reabre; el contenido (etiquetas y repartos) **se conserva** y ya se puede editar | ☐ | |
| 10 | Preparar de nuevo la **misma** selección sobre la guía reversada/anulada | Se crea un documento **nuevo** (clave distinta) con **«Imputación de origen»** = el documento anterior; el terminal **no** cambia | ☐ | |
| 11 | **Aplicar** la nueva operación | Se aplica; el documento de origen muestra «Reversada por» = la nueva | ☐ | Cadena de corrección |
| 12 | Reversar en **dos pestañas** el mismo aplicado con motivos distintos | Sólo una revesra se registra; la otra avisa del conflicto **sin** cambiar usuario/fecha/firma | ☐ | Concurrencia |
| 13 | Verificar que `IMP02220` e `IMP04823` conservan **estado**, **valores** y **clave documental** | Sin cambios respecto al paso inicial | ☐ | |

---

## Qué reportar si algo no cuadra

(a) el número del paso; (b) captura de pantalla; (c) la referencia del documento (`IMP…`) y la etiqueta SV (`SV…`);
(d) la hora aproximada. Con eso se cruza con la bitácora (`madenat.audit.log`) y con los registros de la operación.

**Recordatorio:** esta revisión es de **sólo lectura** salvo los borradores de prueba que se creen (que deben
**anularse**, no aplicarse). No se tocan datos reales de producción, ni `IMP02220`, ni `IMP04823`.
