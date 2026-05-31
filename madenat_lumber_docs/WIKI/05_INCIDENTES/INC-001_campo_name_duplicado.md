# INC-001 — Campo name duplicado en madenat_guia_processing

**Fecha detectado:** 2026-05-12
**Módulo afectado:** madenat_lumber_core
**Severidad:** Medio
**Estado:** Resuelto

## Síntoma

```
odoo.models: Field name already exists on model madenat.guia.processing
```

## Causa raíz

El modelo `madenat_guia_processing.py` definía el campo `name` de forma explícita, mientras que al mismo tiempo heredaba `mail.thread`, que ya provee ese campo. Redefinición silenciosa reportada como warning.

## Solución aplicada

Eliminar la declaración manual del campo `name` en `madenat_guia_processing.py` y dejar que `mail.thread` lo provea. Si el campo necesitaba comportamiento distinto, renombrarlo con prefijo `madenat_`.

## Archivos modificados

- `custom_addons/madenat_lumber_core/models/madenat_guia_processing.py`

## Prevención

Regla permanente: nunca redefinir campos que ya existen en clases padre heredadas via `_inherit`. Ver [[tracking_mail_thread]] y [[herencia_odoo_modelos]].

## Relacionado

- [[tracking_mail_thread]]
- [[herencia_odoo_modelos]]
- [[DEC-003_tracking_sin_chatter]]
