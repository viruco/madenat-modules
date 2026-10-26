# Línea base C2 — suites de `madenat_lumber_core` y `madenat_lumber_logistics`

**Versión documental:** 1.0.0
**Fecha:** 2026-10-26
**Alcance:** línea base de pruebas sobre una **copia** de `madenat_test`. No se ejecutó `-u` ni `-i`, no se
tocó `madenat_test` y la copia se eliminó al terminar.

## 1. Clonación

El servicio web está conectado a `madenat_test`, así que `CREATE DATABASE … TEMPLATE` no es viable. Se usó
copia lógica:

```
docker exec odoo18_db pg_dump -U odoo -Fc madenat_test \
  | docker exec -i odoo18_db pg_restore -U odoo -d madenat_test_c2_20261026 --no-owner --no-privileges
```

Paridad comprobada antes de ejecutar (original vs copia):

| Métrica | `madenat_test` | `madenat_test_c2_20261026` |
|---|---|---|
| Tablas en `public` | 620 | 620 |
| Módulos instalados | 88 | 88 |
| `res_users` | 12 | 12 |
| `stock_move` | 166 | 166 |

## 2. Ejecución

```
docker exec odoo18_app odoo --config=/etc/odoo/odoo.conf \
  --database=madenat_test_c2_20261026 --db-filter='^madenat_test_c2_20261026$' \
  --http-port=8099 --http-interface=127.0.0.1 \
  --test-enable --test-tags=/madenat_lumber_core,/madenat_lumber_logistics \
  --stop-after-init --log-level=test
```

Sin `-u`: el registro se carga tal como está en la base, por indicación del encargo.

## 3. Resultado

| Métrica | Valor |
|---|---|
| Tests lanzados | **1.067** (510 en `madenat_lumber_core`, 557 en `madenat_lumber_logistics`) |
| `odoo.tests.stats` | core: 644 tests, 82,22 s, 50.407 consultas · logistics: 667 tests, 150,20 s, 103.337 consultas |
| Resultado global | **1 failed, 7 error(s) of 1067 tests** |
| Omitidos (`skipTest`) | 3 |

### Rojos preexistentes

| # | Test | Tipo | Causa exacta |
|---|---|---|---|
| 1 | `TestSvConcurrency.test_01_dos_transacciones_no_sobreconsumen` | FAIL | `AssertionError: 2 != 1` en `test_sv_concurrency.py:265`: las dos transacciones concurrentes aplican la rebaja. Falla **ya documentada** como diferida en `CANON/05` (H1-D, HG-07). |
| 2 | `TestResolveExportWidthAPI.test_14_manual_override_validation_and_propagation` | ERROR | `null value in column "conciliation_status" of relation "madenat_guia_processing"` al crear la guía. |
| 3-8 | `TestH5NominalWidthAndStockNotice.test_01…test_06` (6) | ERROR | Misma causa que el nº 2, en `setUp`. |

**Causa común de los 7 errores.** La columna `conciliation_status` de `madenat_guia_processing` está en la
base como `NOT NULL` **sin valor por defecto**, y el campo **no existe en el código**:

```
grep -rn 'conciliation_status' --include='*.py' --include='*.xml' .
→ solo aparece en madenat_lumber_core/tests/test_lumber_reception.py (que comprueba
  `if 'conciliation_status' in GuiaModel._fields` antes de usarlo)
```

Es **deriva de esquema**: la columna quedó de una versión anterior del campo y, al ejecutar **sin `-u`**, el
ORM no la reconcilia, de modo que cualquier `create()` de una guía falla. No es un fallo del código actual,
pero **tampoco está demostrado que desaparezca con `-u`**: la comprobación sería
`odoo -d <clon> -u madenat_lumber_core --stop-after-init` sobre una copia y repetir los dos casos. **No
ejecutado en esta fase** (fuera del alcance autorizado).

**Errores registrados que no cuentan como rojo.** El log contiene además
`null value in column "reason" of relation "madenat_sv_operation"` y `… "madenat_sv_rename_wizard"`: son
transacciones internas revertidas dentro de pruebas que terminan en verde (el resumen de `unittest` sigue en
8 rojos).

### Omitidos

`TestConsolidationImportWizard.test_01`, `test_02` y `test_03` se omiten con aviso porque el `.xlsx` de
referencia no existe **dentro del contenedor**: las rutas están escritas como absolutas del host
(`/home/viruco/dev-stack/…`), que no está montado en `odoo18_app` (solo `config/`, `custom_addons/` y
`/var/lib/odoo`).

## 4. Limpieza

```
DROP DATABASE madenat_test_c2_20261026                   → OK
rm -rf /var/lib/odoo/filestore/madenat_test_c2_20261026  → OK (1,3 MB, 5 archivos generados por las pruebas)
```
## 5. Diff propuesto para las líneas 65-66 — **NO APLICADO**

Objetivo: que la clase se omita **una sola vez, con aviso en el log**, en lugar de tres omisiones sueltas, y
que las rutas se resuelvan también dentro del contenedor (sin depender del host).

```diff
--- a/madenat_lumber_logistics/tests/test_consolidation_import_wizard.py
+++ b/madenat_lumber_logistics/tests/test_consolidation_import_wizard.py
@@ -8,9 +8,22 @@
 5. Invarianza: no crea lotes ni modifica volúmenes en BD.
 """
 import base64
+import logging
 import os
+import unittest
 from odoo.tests.common import TransactionCase
 from odoo.exceptions import UserError

+_logger = logging.getLogger(__name__)
+
+
+def _first_existing(*paths):
+    """Devuelve la primera ruta existente, o None."""
+    for path in paths:
+        if path and os.path.exists(path):
+            return path
+    return None
+

 class TestConsolidationImportWizard(TransactionCase):

@@ -62,9 +75,32 @@ class TestConsolidationImportWizard(TransactionCase):
             'piezas': 250,
         })

-        # Rutas de los archivos reales de referencia
-        cls.path_fa543r = '/home/viruco/dev-stack/odoo/odoo-18-ce/muestras_documentos_ingreso/Ejercicio Completo Cristhian Elgueta/LISTADO TARJAS MN MSC ELENOIRE FA543R.xlsx'
-        cls.path_fa610r = '/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_docs/RAW/LISTADO Y TARJAS MN MSC VIRGO FA610R.xlsx'
+        # Rutas de los archivos reales de referencia. Se prueban varios
+        # candidatos porque las rutas absolutas del host no existen dentro del
+        # contenedor de Odoo (solo se montan config/, custom_addons/ y el
+        # filestore). Si ninguno existe, la clase completa se omite con aviso.
+        stack_root = os.environ.get(
+            'MADENAT_STACK_ROOT', '/home/viruco/dev-stack/odoo/odoo-18-ce')
+        addons_root = os.path.dirname(os.path.dirname(os.path.dirname(
+            os.path.abspath(__file__))))
+        docs_root = os.path.join(addons_root, 'madenat_lumber_docs')
+
+        cls.path_fa543r = _first_existing(
+            os.path.join(stack_root, 'muestras_documentos_ingreso',
+                         'Ejercicio Completo Cristhian Elgueta',
+                         'LISTADO TARJAS MN MSC ELENOIRE FA543R.xlsx'),
+            os.path.join(docs_root, 'RAW',
+                         'LISTADO TARJAS MN MSC ELENOIRE FA543R.xlsx'),
+        )
+        cls.path_fa610r = _first_existing(
+            os.path.join(stack_root, 'custom_addons', 'madenat_lumber_docs',
+                         'RAW', 'LISTADO Y TARJAS MN MSC VIRGO FA610R.xlsx'),
+            os.path.join(docs_root, 'RAW',
+                         'LISTADO Y TARJAS MN MSC VIRGO FA610R.xlsx'),
+        )
+
+        if not cls.path_fa543r:
+            msg = ('TestConsolidationImportWizard omitido: no se encontró el '
+                   'xlsx de referencia FA543R (buscado en MADENAT_STACK_ROOT y '
+                   'en madenat_lumber_docs/RAW).')
+            _logger.warning(msg)
+            raise unittest.SkipTest(msg)
```

Notas sobre el diff:

- Las tres comprobaciones `if not os.path.exists(self.path_fa543r): self.skipTest(...)` de las líneas 70-71,
  96-97 y 138-139 **se dejan como están** (defensa redundante, no estorban).
- El `.xlsx` de FA543R **no está versionado** (`RAW/*.xlsx` está en `.gitignore` y el fichero de
  `muestras_documentos_ingreso/` no está en el repo), así que con este diff la clase seguirá omitiéndose
  dentro del contenedor: el cambio mejora el mensaje y evita 3 omisiones separadas, **no** recupera la
  cobertura. Para recuperarla habría que versionar el fichero (47.814 B) o montarlo en el contenedor.


Bases `madenat_test*` restantes: `madenat_test`, `madenat_test_core`, `madenat_test_fresh`, `madenat_test_ref`
(las tres últimas son preexistentes).
