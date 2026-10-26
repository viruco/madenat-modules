# PLAN DE APLICACIÓN Y REVERSIÓN (para aprobación posterior)

> **NO aplicar todavía.** La aplicación al árbol activo y, con mayor razón, la eliminación
> real de la guía requieren **autorización posterior, específica y separada** de este
> desarrollo.

## 1. Archivos modificados y justificación

| Archivo | Diff | Justificación |
|---|---|---|
| `madenat_lumber_intake/models/intake_guide_lifecycle_wizard.py` | `01` | Atribución por relaciones; clasificación propio/ambiguo/ajeno; mensajes específicos; revalidación inmediata; candado de concurrencia; campo `attribution_notes` |
| `madenat_lumber_intake/views/intake_guide_lifecycle_wizard_views.xml` | `01` | Mostrar `attribution_notes` (no bloqueante) junto a los bloqueadores |
| `madenat_lumber_intake/tests/__init__.py` | `01` | Registrar el nuevo test |
| `madenat_lumber_intake/tests/test_guide_lifecycle_delete_attribution.py` | `01` | Matriz de pruebas de la eliminación (nuevo) |
| `madenat_lumber_core/models/madenat_guia_processing.py` | `02` | Corrección preventiva: `guia_processing_id=False` en los `create` de retorno (reversa BT-04, reversa SV, reversa Modo B) |

Diffs: `patch/01_delete_attribution.diff`, `patch/02_preventive_return_fk.diff`
(unificados `diff -u -p`, aplicables con `git apply` o `patch -p1` desde `custom_addons/`).

## 2. Orden de aplicación propuesto

1. **Base de datos primero (no lo hace este parche):** decidir **D-POL-1** y el destino de
   la cadena 436→7813→7814 (solo lectura en esta fase).
2. Aplicar **`02_preventive_return_fk.diff`** (corrección preventiva, independiente).
3. Aplicar **`01_delete_attribution.diff`**.
4. `-u madenat_lumber_core,madenat_lumber_intake` en un entorno **de pruebas** y correr
   `run_iso.sh`. Debe dar `0 failed, 0 errors`.
5. Revisión de seguridad (grupos/ACL sin cambios) y de la vista.
6. Autorización separada para el borrado **operativo** real de la guía elegible.

## 3. Reversión

* **Código:** revertir con `git apply -R` (o `patch -R -p1`) los diffs correspondientes,
  en orden inverso (01 y luego 02). El parche **no** altera datos ni esquema, así que la
  reversión de código es suficiente.
* **Datos:** no aplica (no hay migración). Los tests usan `TransactionCase` (rollback). El
  único efecto persistente posible sería un `madenat.audit.log` de una eliminación real,
  que es append-only por diseño (evidencia, no borrado).

## 4. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Un histórico propio sin FK ni lotes se clasifica **ambiguo** (bloquea) | Es el comportamiento seguro: bloqueo explicable, no borrado silencioso |
| Ventana validación→borrado con concurrencia real | Revalidación inmediata + `pg_advisory_xact_lock`. **Queda una ventana residual** si otro proceso **crea** una dependencia (no toma el mismo candado); se propone como mejora futura `SERIALIZABLE`/FK de dominio (**no implementado**, requiere aprobación) |
| `attribution_notes` expone nombres ajenos | Solo se muestran **conteos** de ajenos (no nombres); los nombres solo aparecen para propios/ambiguos (documentos de la propia guía) |
| Interacción con `IMPL_SERVICE_RETURN_20261006/` | Diffs **separados**; repetir la regresión 53/53 de aquel trabajo al converger |

## 5. Criterios de aceptación (verificados en aislamiento)

* [x] Guía cancelada realmente elegible se elimina desde Modo A.
* [x] Un documento ajeno no bloquea solo por compartir número.
* [x] Un retorno propio/ambiguo no queda invisible.
* [x] Diagnóstico y ejecución coinciden (mismo criterio).
* [x] No se modifica stock ni contabilidad para facilitar el borrado.
* [x] No se debilitan permisos ni protecciones.
* [x] Sin cambios en el árbol/base activos.
* [ ] UI real (navegador) — **pendiente** (declarada).
