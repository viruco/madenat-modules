# APPLY_BUSQUEDA_INTAKE_20261007 — Aplicación en madenat_test

Aplicación de la mejora mínima de búsqueda de Intake **únicamente en el entorno
local `madenat_test`**. **Sin** despliegue a producción. **Sin** commit/push.
**Sin** reordenamiento para instalación limpia (queda como trabajo separado).

Artefacto aplicado: `IMPL_BUSQUEDA_INTAKE_20261007` (gate: `gate == artifact`).

## Contenido

```
APPLY_BUSQUEDA_INTAKE_20261007/
├── backup/
│   ├── intake_module_pre.tar.gz          Código pre-cambio (módulo intake)
│   ├── wip_uncommitted.diff              git diff HEAD (cambios locales previos)
│   ├── git_status_pre.txt / _post.txt    Estado Git antes/después (58 entradas)
│   ├── madenat_test_pre.dump             pg_dump -Fc (13325 TOC entries, 11 MB)
│   └── filestore_madenat_test_pre.tgz    filestore madenat_test (21 MB)
├── docs/
│   ├── BACKUP_APLICACION.md              Qué se respaldó y cómo restaurar
│   ├── VERIFICACION_POST_APLICACION.md   Verificación no destructiva (SQL + ORM)
│   └── GUION_VERIFICACION_NAVEGADOR.md   Guion V3 (browser)
├── logs/
│   ├── update_madenat_test.log           Update controlado (0 ERROR)
│   ├── verify_orm.txt / _resultados.txt  Salida de `odoo shell`
│   └── hashes_activo_post.txt            MD5 de los archivos aplicados
└── README.md
```

## Resumen

- **Archivos aplicados** (solo `madenat_lumber_intake`): `models/intake_console.py`,
  `views/intake_console_views.xml`, `tests/__init__.py`, + `tests/test_search_console_oc_fecha_modality.py`.
- **Update controlado** de `madenat_lumber_intake` en `madenat_test`: **0 errores**;
  `Registry loaded in 11.6s`. Servicio reiniciado → **HTTP 200**.
- **Verificación no destructiva**: vista con 14 columnas; 18 filas = 18 ids distintos
  (sin duplicación); búsquedas/agrupaciones/navegación OK; offset de IDs intacto.
- **V3 (navegador) PENDIENTE** hasta comprobación real (ver guion).
