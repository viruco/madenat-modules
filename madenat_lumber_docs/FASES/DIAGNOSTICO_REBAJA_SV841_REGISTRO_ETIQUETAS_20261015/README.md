# DIAGNÓSTICO — REGISTRO DE ETIQUETAS EN «REBAJA DE ETIQUETAS» (SV00000000841 / IMP04823) — 2026-10-15

**Informe completo:** [`INFORME_DIAGNOSTICO.md`](INFORME_DIAGNOSTICO.md)
**Evidencia:** [`evidence/`](evidence) (scripts `repro_1…repro_7`) · [`logs/`](logs) (`reproduccion.log`, `baseline.log`)

**Alcance:** SOLO LECTURA + reproducción en transacción **REVERTIDA** (`odoo shell` con `env.cr.rollback()`).
**Sin commit · sin push · sin cambios de código/datos/vistas/ACL · sin `-u` · sin TEST remoto.**
No se tocó `IMP04823` (id 2733) ni `IMP02220` (id 1189).

## Resultado en una línea

El registro de etiquetas **funciona** en un caso sano (demostrado: `draft → applied` con reparto persistido);
en el caso reportado falla por **tres defectos preexistentes**: **(F1)** la clave documental no incluye la
selección de etiquetas y `_i2_get_or_create` reutiliza por clave **sin filtrar estado** ⇒ para la guía 1198
colisiona con `IMP02220` (**aplicada**) y el guardado se rechaza; **(F2)** la sección «Trabajo en preparación»
**no filtra en el servidor** (el `domain` del O2M no se aplica al leer) y su contador **cuenta anulados/aplicados**;
**(F3)** «Guardar borrador» admite documentos **sin ninguna etiqueta** (sin aviso).

Ninguno proviene de las FASES 5–8 ni del WIP: las funciones implicadas son **idénticas en HEAD y en el WIP**
(`_i2_build_documentary_key`, `_i2_get_or_create`, `_i2_signature`, `_i2_included_lines`, `_i2_processed_lots`) y
existen desde el commit `2888745` (2026-10-02, I2/AD-91).

## Estado de la base al cierre (§7 del informe)

`git status` = **11 entradas** · HEAD `677294b` · huella del WIP **idéntica** (byte a byte) ·
`madenat_test` = 13 guías / 151 lotes / 327 auditorías / 3 imputaciones / 3 líneas / 1 reparto ·
`IMP04823` intacta (`cancelled`, 0 líneas) · lote 10215 y sus quants intactos.
