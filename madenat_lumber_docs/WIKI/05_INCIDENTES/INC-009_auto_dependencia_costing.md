# INC-009: Auto-dependencia circular en `madenat_lumber_costing`

**ID:** INC-009
**Fecha:** Resuelto antes de 2026-06-06 (documentado 2026-06-06)
**Estado:** RESUELTO
**Severidad:** Alta (carga de módulo)
**Módulo afectado:** madenat_lumber_costing

---

## Síntoma

Error o advertencia al instalar `madenat_lumber_costing`: un módulo no puede depender de sí mismo.

## Causa raíz

El `__manifest__.py` de costing incluía `'madenat_lumber_costing'` en su lista de `depends`. Esto crea una dependencia circular trivial (un módulo dependiendo de sí mismo).

## Solución

Eliminar `'madenat_lumber_costing'` de la lista `depends`. El manifiest actual tiene un comentario documentando la corrección:
```python
# 🛑 ELIMINADO: 'madenat_lumber_costing' (Un módulo no puede depender de sí mismo)
```

## Archivos modificados

`madenat_lumber_costing/__manifest__.py` — línea 23 (comentario) + eliminación de la dependencia

## Verificación

La lista `depends` actual es: `['account', 'madenat_lumber_core', 'madenat_lumber_logistics', 'madenat_lumber_shipping_core']` — correcta, sin auto-referencia.

## Relacionado

- AUDITORIA_INTEGRAL_2026-06-06.md — Fortaleza M4