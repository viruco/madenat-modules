# IDENTIDAD DE REVISIÓN E ISOLAMIENTO

FIX de eliminación de ingresos cancelados — MADENAT (Odoo 18 CE).
Carpeta de entrega: `FIX_DELETE_INTAKE_20261007_145130/` (NUEVA; no es el árbol activo).

## 1. Qué cambió desde la auditoría `AUDIT_DELETE_INTAKE_20261007_130559`

| Dato | Valor |
|---|---|
| Raíz Git | `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` (la raíz `odoo-18-ce` **no** es Git) |
| HEAD | `e302c488321c276af7e07f1abeecc8bc261a89f4` (idéntico al de la auditoría) |
| Estado de los archivos intervenidos | **tracked-unmodified** (idénticos a HEAD; `git status` vacío para ellos) |

**Hashes SHA-256 — host == contenedor== auditoría (no hubo deriva):**

| Archivo | SHA-256 | ¿Coincide con la auditoría? |
|---|---|---|
| `madenat_lumber_intake/models/intake_guide_lifecycle_wizard.py` | `6baa7b84549ffe805f6532a681888702dbc6f222ae74687dd6ce2d43ee93aed9` | ✔ (INVENTARIO.csv) |
| `madenat_lumber_core/models/madenat_guia_processing.py` | `b86230d2f3043f82c1ac555d82a2dc683b63a5d74f207deadddbaac36ada3596` | ✔ |
| `madenat_lumber_intake/views/intake_guide_lifecycle_wizard_views.xml` | `5a11e3de13f5aa99ba36a432fd2ae6a3b871cfd23acbb25cf1ba7eb250a9143d` | ✔ |
| `madenat_lumber_intake/tests/__init__.py` | `3361a28c6b15243502f217cd91a215b806e0b30b317eb2377ca7eebb99b7f46f` | ✔ |

> Conclusión: el parche se calcula **contra la revisión ya auditada** (`e302c488`). No se repite la auditoría general.

## 2. Material auditado reutilizado (no re-empaquetado)

`AUDIT_DELETE_INTAKE_20261007_130559/`: `IDENTIDAD_REVISION.md`, `MAPA_ELIMINACION.md`,
`DICTAMEN.md`, `PLAN_VALIDACION.md`, `INVENTARIO.csv`, `sources/`. Se reutilizan como
punto de partida; el hallazgo diferencial reproducido aquí es la **fuga de
`guia_processing_id` por contexto** (ver `02_preventive_return_fk.diff`).

## 3. Isolamiento verificado

| Elemento | Valor |
|---|---|
| Base de datos | **`delint_test_20261007`** (clon `CREATE DATABASE … TEMPLATE srvret_test_20261006`). `madenat_test` y producción **no** se tocaron. |
| Código | `FIX_DELETE_INTAKE_20261007_145130/addons` montado en `/mnt/extra-addons:ro`. El árbol activo `custom_addons` **no** se modifica. |
| Proceso | Contenedor one-shot `delint_iso` (`--rm`), red `odoo-18-ce_internal_backend`, filestore interno efímero. |
| Salvaguardas | `--max-cron-threads=0 --workers=0 --no-http --stop-after-init --test-enable`. Sin SMTP ni integraciones. |
| Comando | `run_iso.sh` (ver §4). |
| Log | `logs/iso_run2.log` (definitivo; `logs/iso_run.log` = 1ª iteración con fallos de test, ver `RESULTADOS`) |

No se reinició ningún servicio activo; no se aplicó el parche al árbol activo; no se
ejecutó SQL de escritura manual ni `sudo()`.

## 4. Comando de ejecución

```bash
# clon de la base de prueba (nunca madenat_test)
docker exec odoo18_db psql -U odoo -c \
  "CREATE DATABASE delint_test_20261007 TEMPLATE srvret_test_20261006 OWNER odoo;"
# ejecución aislada
bash FIX_DELETE_INTAKE_20261007_145130/run_iso.sh
```

## 5. Límites de evidencia (declarados)

1. El clon se hizo desde `srvret_test_20261006` (clon lógico de `madenat_test`); los datos
   del caso real **33152 / 15183 / 7813** no están replicados con sus IDs reales.
   El caso se **reproduce con fixtures equivalentes** (documento ajeno homónimo, FK
   directa, retorno vinculado), no invocando el registro real.
2. **UI:** no hubo clic de navegador auditado; el cierre del asistente y el refresco se
   verifican por el `action` devuelto (`_console_reload_action`) y por la vista XML, no
   por una sesión real de Owl.
3. La reproducción del caso 15183 es **por equivalencia** (ver `RESULTADOS`, §“Caso 15183”).
