# INC-010 — thickness_visual 6/4: 45mm S2S clasificaba como 7/4

**Fecha:** 2026-06-11
**Módulo:** madenat_lumber_core
**Versión fix:** 18.0.5.1.0
**Commits:** `3252c7e`, `52ec1c7`
**Detectado en:** TEST (guía 40601 — 12 lotes 45mm)

## Síntoma
Lotes con espesor físico `45mm` mostraban `thickness_visual = 7/4`
en lugar del valor correcto `6/4`.

## Causa raíz
El rango de `6/4` terminaba en `42mm`, dejando `45mm` (espesor S2S
canónico de 1.5" nominal) fuera del rango y cayendo en `7/4`.

| Regla | Campo | Antes | Después |
|-------|-------|-------|---------|
| `6/4` | `max_thickness` | 42.0 mm | 46.0 mm |
| `7/4` | `min_thickness` | 42.0 mm | 46.0 mm |

## Archivos modificados
- `madenat_lumber_core/data/thickness_visual_ranges_seed.xml`
- `madenat_lumber_core/migrations/18.0.5.1.0/post-migrate.py`
- `madenat_lumber_core/__manifest__.py` (version bump 5.0.0 → 5.1.0)

## Fix aplicado
Script de migración idempotente en `post-migrate.py`:
```sql
UPDATE lumber_thickness_visual_rule
   SET max_thickness = 46.0
 WHERE visual_label = '6/4' AND max_thickness < 46.0;

UPDATE lumber_thickness_visual_rule
   SET min_thickness = 46.0
 WHERE visual_label = '7/4' AND min_thickness < 46.0;
```

## Validación
- Local `madenat_test`: ✅ `0 rows` (corregido manualmente antes del upgrade)
- TEST remoto `144.22.50.236`: ✅ corregido vía SSH
- Producción: ⏳ pendiente deploy → espera `(1 rows)` en logs
