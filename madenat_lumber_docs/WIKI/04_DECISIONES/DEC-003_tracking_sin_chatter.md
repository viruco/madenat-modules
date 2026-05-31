# DEC-003 — Resolución de Duplicado en mail.thread

**Fecha:** 2026-05-12
**Estado:** Aceptada
**Módulo afectado:** madenat_lumber_core

## Contexto

`madenat_guia_processing.py` redefinía el campo `name` ya existente por herencia de `mail.thread`. Generaba warnings y riesgo de inconsistencia.

## Decisión tomada

Eliminar la redefinición manual del campo `name`. Regla establecida: nunca redefinir campos heredados de `mail.thread`.

## Impacto

- Desaparecen warnings en logs.
- Chatter funciona sin campo duplicado.

## Criterio de revisión

Aplica a cualquier modelo futuro que herede `mail.thread` en MADENAT.

## Referencias

- [[tracking_mail_thread]]
- [[herencia_odoo_modelos]]
- [[INC-001_campo_name_duplicado]]
