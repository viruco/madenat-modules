# DEC-006 — Uso de post-migrate.py para corrección de datos maestros

**Fecha:** 2026-06-11
**Contexto:** Fix INC-010 thickness_visual 6/4

## Decisión
Todo fix que modifique datos maestros con `noupdate="1"` o que requiera
garantía de ejecución automática en cualquier ambiente **debe incluir
un script `migrations/X.Y.Z/post-migrate.py`** además del XML corregido.

## Razón
Un `UPDATE` manual en DB no es reproducible ni auditable.
El seed XML con `forceCreate="True"` sobreescribe en upgrade, pero
depende del orden de carga y no deja trazabilidad en logs de Odoo.
El `post-migrate.py` es ejecutado por Odoo exactamente una vez,
queda en log y es idempotente si se usan guards `WHERE`.

## Patrón estándar
```python
# migrations/18.0.X.Y.Z/post-migrate.py
def migrate(cr, version):
    cr.execute("""
        UPDATE tabla SET campo = valor
         WHERE condicion AND campo != valor;  -- guard idempotente
    """)
    _logger.info("Migration X.Y.Z: descripción (%d rows)", cr.rowcount)
```

## Consecuencia
- Version bump obligatorio en `__manifest__.py`
- Entrada en `CHANGELOG.md`
- Entrada en `WIKI/05_INCIDENTES/` si viene de un bug
