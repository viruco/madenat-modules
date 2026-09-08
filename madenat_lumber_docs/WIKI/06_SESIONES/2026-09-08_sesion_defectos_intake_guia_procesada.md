# Sesión 2026-09-08 — Defectos de Intake y Guía Procesada

## Resumen ejecutivo

Se diagnosticaron y corrigieron 3 defectos, y se documentó 1 pendiente:

| Defecto | AD | Estado |
|---|---|---|
| A: regex RUT solo "con puntos" en `reception_parser` (flujo Producto) | AD-60 | ✅ Corregido |
| C: routing por nombre de archivo en vez de contenido (wizard Intake) | AD-61 | ✅ Corregido |
| T/C: tipo de cambio ausente bloqueaba ingreso a stock (service) | AD-62 | ✅ Corregido |
| B: bloqueo `UserError` ante RUT ausente en flujo Producto (`lumber_reception.py` L2302-2306) | — | ⏳ Documentado, **NO resuelto** |

## Caso real que originó el diagnóstico

Guía **26270** (COMERCIALIZADORA Y DISTRIBUIDORA FERRAMENTA SPA, RUT `77066489-6`, servicio de cepillado):

- El registro fue creado **erróneamente en `lumber.reception`** (id=1448) por el
  enrutamiento basado en nombre de archivo (antes de AD-61), con **0 líneas
  persistidas** y **sin efectos en inventario** (0 lotes, 0 pickings, 0 moves,
  0 quants, `audit_hash`/`audit_snapshot` NULL).
- El PDF 26270 **no trae la línea "T/C U$"** (tipo de cambio), por lo que
  bloqueaba el ingreso a stock con `rate_usd=1.0` (corregido en AD-62).

## Estado pendiente de 1448

El registro `lumber.reception` **id=1448** (26270) sigue existiendo, **sin
cancelar**, esperando autorización explícita del Product Owner.

## Hallazgo de gobernanza

Se detectó un cambio de código **sin commit ni autoría trazable** en el working
directory (el `invisible="1"` del campo `tipo_ingreso`), que generó horas de
investigación innecesaria. Recomendación: disciplina de **commits pequeños y
frecuentes** para evitar este problema a futuro.

## Archivos modificados por AD

| AD | Archivos |
|---|---|
| AD-60 | `madenat_lumber_core/models/reception_parser.py`, `madenat_lumber_core/tests/test_reception_supplier_rut_extraction.py`, `madenat_lumber_core/tests/fixtures/26270.txt`, `madenat_lumber_core/tests/__init__.py`, `04_DECISION_LOG.md` (entrada AD-60) |
| AD-61 | `madenat_lumber_intake/models/intake_wizard.py`, `madenat_lumber_intake/views/intake_wizard_views.xml`, `madenat_lumber_intake/tests/test_intake_tipo_ingreso_content.py`, `madenat_lumber_intake/tests/__init__.py`, `04_DECISION_LOG.md` (entrada AD-61) |
| AD-62 | `madenat_lumber_core/models/madenat_guia_processing.py`, `04_DECISION_LOG.md` (entrada AD-62), este documento |
