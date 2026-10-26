# Matriz de alineación documental (Regla → fuente → actual → propuesto → estado)

Doctrina vigente usada: `CANON/00`, `CANON/04` (AD-80, AD-88), `CANON/12` (§2, §5.2,
§6.2, §11.5–11.7), `CANON/17` (§1–§2). `RAW/`, `LEGADO/`, `WIKI/06_SESIONES` y
`_archive_*` se tratan como **histórico/propuesta**, no como política.

| # | Regla | Archivo · sección | Comportamiento ACTUAL (parche previo) | Comportamiento PROPUESTO | Estado |
|---|---|---|---|---|---|
| 1 | **Identidad de una guía** = `name` + `partner_id`; el número **no** es clave global | `CANON/12 §2`, `§3.3`; `CANON/12 §5.2` (`guia_number` informativo) | Bloqueo confirmado solo en el mismo modelo (guía) | Igual: bloqueo confirmado = mismo `name` + mismo `partner_id` conocido (mismo modelo) | ✅ Compatible |
| 2 | **Homónimos entre modelos**: el número se repite entre flujos (recepción ↔ guía) | `CANON/12 §5.2`, `§6.2` (26 lotes con `guia_number` coincidente) | **Asimetría**: la guía no bloqueaba cross-model; la Recepción **sí** (`cross_model=True`) | **No bloquea cross-model en ningún sentido** (simétrico) + aviso no bloqueante | ✅ Compatible (corrige asimetría) |
| 3 | **Captura incompleta** (borrador) permitida | `CANON/00 §4.3` (estados draft); `12 §11.5` (bloqueos son al salir a stock) | Bloqueaba por número cuando `partner_id` nulo (postura conservadora) | **No bloquea** identidad incompleta; conserva; **revalida al completar** | ✅ Compatible (AJUSTE A) |
| 4 | **Corrección y relectura del propio documento** | `CANON/00 §4.2`, `§4.3` (reopen no bloqueante y trazable) | Exclusión propia por modelo+id ya correcta | Igual (self-exclusion por `exclude_model`+`exclude_id`) | ✅ Compatible |
| 5 | **Documentos cancelados** se conservan (trazabilidad) | `CANON/12 §11.7`; `CANON/00 §4.9` (Modo B = cancelar y conservar) | Bloquea igual que cualquier existente (no ignora cancelados) | Igual: un cancelado **sigue** contando como existente | ✅ Compatible |
| 6 | **Particularidades de Volúmenes** (granel): volumen oficial gobierna; sin dimensiones; sin `company_id` en la guía | `CANON/12 §11.5–11.6`; `CANON/17 §1.4` | Identidad de la guía = `name`+`partner` (sin `company_id`); sin cambios de volumen | Igual: no se toca volumen ni dimensiones; solo la identidad documental | ✅ Compatible |
| 7 | **Advertir sin bloquear** (desviaciones) | `CANON/04 AD-88` (mixin `madenat.deviation.mixin`) | No existía aviso en la ingesta | Aviso **no bloqueante** en el chatter (`mail.thread`, mecanismo existente) | 🟡 No definido en detalle (AD-88 exige motivo; aquí es aviso pasivo) |
| 8 | **Validación de duplicados vigente** (control C1) | `CANON/03 §` (test 2026-06-11) | C1 compartido, solo usado por Recepción | C1 reutilizado por la guía; **misma lógica**, sin duplicar | ✅ Compatible |

## Conflictos concretos detectados

- **Conflicto C-a (resuelto):** la recomendación D1 de la auditoría previa
  (`AUDIT_GUIA_DUPLICADOS_20261007` §H) sugería **bloquear** el número homónimo. Eso
  **contradice** `CANON/12 §5.2` (el número no es discriminatorio) y el criterio previo
  «no bloquear documentos distintos solo por número». **Resolución:** el homónimo **no**
  bloquea; se advierte (AJUSTE C). No se cambia la doctrina; se **corrige el parche**.
- **Conflicto C-b (resuelto):** la asimetría `cross_model` (guía no bloquea / Recepción sí)
  no tiene respaldo doctrinal → se elimina imponiendo **simetría** (AJUSTE B).
- **No definido (documentado):** AD-88 describe «advertir + motivar + auditar» para
  decisiones blandas **con motivo**. Un aviso **pasivo** (sin motivo) no está tipificado;
  se usa el canal existente del chatter y se deja constancia como decisión pendiente de
  ratificación.

## Fuera de alcance (no se toca)

`gates` dimensionales de Volumen (`12 §11.6`), volumen oficial (`12 §11.5`, `17`),
ciclo de vida Modos A–D (`12 §11.7`), ACL/grupos, parser de lectura, CANON.
