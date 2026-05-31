# INC-005 — Falta de license en __manifest__.py

**Fecha detectado:** 2026-05-03
**Módulo afectado:** madenat_lumber_core, madenat_lumber_reports
**Severidad:** Bajo
**Estado:** Resuelto

## Síntoma

```
WARNING odoo: Module madenat_lumber_core: Missing `license` key in manifest
WARNING odoo: Module madenat_lumber_reports: Missing `license` key in manifest
```

## Causa raíz

Los archivos `__manifest__.py` no incluían la clave `license`. Odoo 18 la requiere.

## Solución aplicada

```python
{
    'name': 'MADENAT Lumber Core',
    'version': '18.0.5.0.0',
    'license': 'LGPL-3',
    ...
}
```

## Prevención

Todo `__manifest__.py` debe incluir `'license': 'LGPL-3'`. Verificar en checklist de módulo nuevo.

## Relacionado

- [[modulo_lumber_core]]
- [[DEC-001_modularizacion_v5]]
