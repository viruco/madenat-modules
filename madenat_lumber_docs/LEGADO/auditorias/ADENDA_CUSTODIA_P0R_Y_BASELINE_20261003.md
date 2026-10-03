# Adenda de Custodia P0-R y Baseline de Desarrollo

**Fecha de emisión:** 2026-10-03T12:40:14-03:00  
**Repositorio:** `custom_addons`  
**Rama:** `feat/p0-r-core-sv-foundation-remediation-20261002`

## 1. Propósito

Esta adenda formaliza la relación entre el commit funcional validado de P0-R
y el baseline vigente de desarrollo, resolviendo la diferencia de identidad
detectada entre la cadena de custodia y el HEAD posterior de saneamiento.

No reejecuta pruebas, no reconstruye recursos temporales y no altera el
alcance funcional validado de P0-R.

## 2. Commit funcional validado

| Control | Valor |
|---|---|
| Commit P0-R validado | `ac8f25f874679e8eb2b89303fb43711a16d80b22` |
| Mensaje | `test(core): corrige aserción de retorno p0-r` |
| P0-R | 34/34 PASS; 0 failed; 0 errors |
| SV histórico | 58/58 PASS; 0 failed; 0 errors |
| Oráculo físico/ACL | 37/37 PASS |
| Rollback | `rollback_performed=true` |
| Residuo | `residual_zero=true` |
| Dictamen previo | P0-R AUDITADO FORMALMENTE — APTO PARA CIERRE Y GATE DE UPGRADE |

La cadena de custodia ubicada en:

```text
/tmp/p0r_closure_20261003_1216
```

conserva el commit funcional validado `ac8f25f874679e8eb2b89303fb43711a16d80b22` y su manifiesto
de cierre valida por SHA-256.

## 3. Baseline vigente

| Control | Valor |
|---|---|
| HEAD de desarrollo | `0bb5b6473a0432855ce207abae64d79855e82941` |
| Mensaje | `chore(repo): sanea artefactos y documentación` |
| Padre directo | `ac8f25f874679e8eb2b89303fb43711a16d80b22` |
| Base de comparación | `origin/main` |
| Base | `b862415c5e177a869c38acf574b8cd77b236ab06` |
| Relación con P0-R | Descendiente directo, delta no funcional |

El HEAD vigente se adopta como baseline local de desarrollo porque desciende
directamente del commit P0-R validado y no introduce cambios funcionales.

## 4. Delta auditado

El delta entre `ac8f25f874679e8eb2b89303fb43711a16d80b22` y `0bb5b6473a0432855ce207abae64d79855e82941` contiene solamente:

- eliminación de seis archivos rastreados, vacíos (0 bytes) y sin referencias;
- movimiento sin modificación de contenido de dos informes históricos desde la
  raíz del repositorio a `madenat_lumber_docs/LEGADO/auditorias/`.

No contiene cambios en:

```text
models/
wizard/
security/
views/
data/
tests/
__manifest__.py
__init__.py
stock
ACL
Docker
configuración
```

Los seis archivos eliminados estaban vacíos (0 bytes) y no eran referenciados
por manifiestos ni por `__init__.py`:

```text
remove_invalid_field.py                                              (0 bytes)
madenat_lumber_reception_improvements/models/lumber_reception.py     (0 bytes; no importado en models/__init__.py)
madenat_vendor_payment/report/vendor_payment_reports.xml             (0 bytes; no listado en __manifest__.py)
madenat_vendor_payment/report/vendor_payment_templates.xml           (0 bytes; no listado en __manifest__.py)
madenat_vendor_payment/wizards/payment_approval_views.xml            (0 bytes; no listado en __manifest__.py)
madenat_vendor_payment/wizards/vendor_payment_batch_views.xml        (0 bytes; no listado en __manifest__.py)
```

Los informes trasladados preservan su contenido íntegramente (SHA-256 idéntico
origen/destino):

```text
REPORTE_IMPLEMENTACION_LOTES_REPETIDOS_RECEPCION.md                 c310719c95bf82ee80a7fd1b892afae050e641dcca1aeb258ac989018244d115
REPORTE_INVESTIGACION_LOTES_REPETIDOS_RECEPCION_VS_PROCESADOS.md    2a3d555eecb91e0f1c4297b24649062697d7b280eeb97aa38947c1818de3d787
```

Por tanto, este delta no modifica comportamiento productivo, contratos de
stock, seguridad, trazabilidad, modelos, vistas, datos ni la cobertura
funcional ya validada.

## 5. Resolución de hallazgos

### F1 — Diferencia entre HEAD custodiado y HEAD vigente

**Estado:** Resuelto por adenda de alcance.

La custodia P0-R vincula correctamente el commit funcional validado
`ac8f25f874679e8eb2b89303fb43711a16d80b22`. El HEAD vigente `0bb5b6473a0432855ce207abae64d79855e82941` es su hijo directo y
su delta fue auditado como no funcional. No corresponde repetir P0-R, SV
histórico ni el oráculo físico/ACL.

### F2 — Archivo post-cleanup vacío

**Estado:** Evidencia consistente con limitación documental declarada.

El archivo `audit_db_after_cleanup.txt` no contiene filas (0 bytes), lo que es
consistente con una consulta de lectura sobre una base temporal inexistente.
La eliminación de recursos P0-R queda además respaldada por el informe de
limpieza controlada, la ausencia verificada de worktree, logs, filestore y
TMP, y la preservación de `madenat_test`.

La ausencia de texto en el archivo no se interpreta como nueva ejecución ni
como evidencia reconstruida; se declara como limitación documental menor sin
impacto funcional ni de integridad.

## 6. Regla de validación futura

Esta adenda no autoriza cambios funcionales sin pruebas.

| Tipo de cambio posterior | Gate requerido |
|---|---|
| Documentación, archivos vacíos, cachés, backups o movimientos históricos sin cambio de contenido | No reabre P0-R |
| Tests funcionales | Validación focalizada del área afectada |
| `models/`, `wizard/`, `security/`, `views/`, `data/`, `__manifest__.py`, stock o ACL | Gate funcional y dinámico correspondiente |
| Procesado/Reconciliación | Nueva línea de desarrollo con diagnóstico, contrato server-side, ACL, pruebas y validación propios |

## 7. Dictamen

```text
BASELINE DOBLEMENTE VERIFICADO — AUTORIZADO PARA DIAGNÓSTICO DE PROCESADO Y RECONCILIACIÓN
```
