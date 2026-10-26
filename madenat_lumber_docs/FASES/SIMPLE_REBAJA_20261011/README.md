# SIMPLIFICACIÓN OPERATIVA DE LA REBAJA — 2026-10-11

**Solicitud expresa de Mauricio:** «sólo aplicar o guardar lo seleccionado; no complicar el flujo ni
obligar a abrir el documento para aplicar».
**Entorno:** `madenat_test`. **Módulo:** `madenat_lumber_logistics` **18.0.1.19.0 → 18.0.1.20.0**.
**Sin commit/push/despliegue. Sin reparación histórica. Cambios locales ajenos preservados.**

## 1. Recorrido simplificado (una misma ventana)
**Elegir guía → seleccionar material → indicar m³ → [Guardar] o [Aplicar]**, y **[Volver]** para navegar.
No se exige «Preparar asignación», ni Guardar antes de Aplicar, ni abrir el documento, ni cambiar de
pestaña. La simplificación afecta la **interacción**, no las validaciones ni la trazabilidad.

## 2. Botones principales y métodos reales
En el **`<header>`** (formulario amplio `target="current"`):

| Botón | Método | Efecto |
| --- | --- | --- |
| **Guardar** | `action_prepare` | crea/actualiza el documento persistente; **permanece** en la ventana; `save_result` |
| **Aplicar** | `action_apply` | crea/actualiza el documento, **aplica** la rebaja y **permanece**; `apply_result` |
| **Volver** | `action_discard_changes` | vuelve al SV (con `confirm`); no cancela el documento ni libera reservas |

## 3. Cómo Aplicar guarda/sincroniza y aplica sin abrir el documento
`action_apply` → `_i2_build_imputation()` (sincroniza selección/cantidades/reparto y crea/actualiza el
documento) → validaciones existentes → `action_apply` (una sola vez) → `action_link_return_links()` →
`apply_result` («Rebaja IMP… aplicada · X,XXX m³ hacia SV…») → **permanece** (recarga el propio
asistente). No hay navegación obligatoria al documento.

## 4. Cómo Guardar persiste y permite continuar
`action_prepare` → `_i2_build_imputation()` → `save_result` («Borrador IMP… guardado. No se ha aplicado la
rebaja. Las etiquetas seleccionadas mantienen la reserva documental prevista.») → permanece. El documento
queda localizable desde el SV (panel «Trabajo en preparación» → **Continuar**). Guardar repetido
**actualiza** el mismo documento.

## 5. Sincronización interna (sin paso «Preparar»)
La cantidad de la tabla **Materiales** (`cantidad_asignar_m3`, compute+inverse) escribe el reparto hacia el
**SV de trabajo** (`sv_alloc_ids` → `sv_line_ids`); `_i2_build_imputation` lo persiste al Guardar o
Aplicar. **No** hay segunda cantidad independiente ni se sustituyen repartos de otros SV. `action_assign_selected`
(«Preparar asignación») se conserva como **control avanzado** en la tabla, no como etapa obligatoria.

## 6. Opciones avanzadas
Grupo **«Más opciones (avanzado)»** en el mismo formulario: **Abrir documento** (consulta, nunca requisito),
**Dejar pendiente**, **Proponer FIFO**. Métodos conservados. Desde el SV e historial siguen disponibles:
continuar borrador, consultar documento, cancelar no aplicado, consultar aplicado, revertir con motivo
según permisos, historial y nueva asignación trazable.

## 7. Validaciones, atomicidad e idempotencia (preservadas)
Contrato de aplicación (≥1 reparto positivo a SV autorizado), techo duro, integridad etiqueta–guía,
permisos y compañía, inmutabilidad del aplicado, reversa con motivo, advisory locks, idempotencia y
atomicidad **sin cambios**. Un fallo no deja documento parcial, consumo ni reserva huérfana, y no muestra
éxito. Repetir Guardar/Aplicar no duplica.

## 8. Mensajes y material sin disponibilidad
- Sin reparto positivo **con** disponibilidad: **«Indica los m³ a rebajar en las etiquetas seleccionadas.»**
- Sin reparto positivo **sin** disponibilidad: **«Las etiquetas seleccionadas no tienen disponibilidad.
  Consulta la operación que las compromete o selecciona material disponible.»**
- Exceso: el `constraint` nombra etiqueta, reparto y nominal autorizado.
- Fila cero: no es reparto positivo (permite Guardar, **no** Aplicar); **cantidad negativa se rechaza**.
- La tabla muestra la **causa real** del saldo y el acceso a los documentos consumidores.

## 9. Pruebas y regresión
Suite nueva `tests/test_sv_rebaja_simple.py` (**SIMPLE-01..17** + **CLIENT-01..03**): botonera de dos
acciones; aplicar sin Guardar ni Preparar; guardar en la misma ventana; continuar; repetir sin duplicar;
cero/negativo/exceso; sin disponibilidad; otros SV conservados; «Usar disponible»; descartar; resultado y
bloqueo tras aplicar; permisos/compañía; reversión; sin efectos físicos; cantidad editada al reparto.

Comando y resultado (base `madenat_test`):
```
odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http \
     --http-port=8071 --test-tags /madenat_lumber_logistics
# → ver logs/regression.log (mismas fallas preexistentes)
```

## 10. Evidencia de navegador
**Sin navegador en el entorno** ⇒ límite declarado; **no** se afirma aceptación operativa. Guion breve en
`docs/GUION_NAVEGADOR_SIMPLE.md`.

## 11. Versión instalada
`madenat_lumber_logistics` **18.0.1.20.0** en `madenat_test` (sólo este módulo; sin `-u all`).

## 12. Documentación
CANON `19` §19.26, `02` §17.16.24, `03` §28, índice.

## 13. Archivos afectados y cambios ajenos
`wizards/madenat_sv_imputation_wizard.py`, `wizards/madenat_sv_imputation_wizard_views.xml`,
`models/madenat_sv_imputation.py` (mensaje de validación), `tests/test_sv_rebaja_ui_limpia.py`,
`tests/test_sv_rebaja_ui_acciones.py`, `tests/__init__.py`, `__manifest__.py`, `CHANGELOG.md`, nuevo
`tests/test_sv_rebaja_simple.py`. WIP ajeno **preservado**.

## 14. Pendientes
1. **Aceptación en navegador** (guion SIMPLE).
2. **Sobrescritura concurrente de borradores**: «última escritura gana», sin bloqueo optimista — **sigue
   como riesgo pendiente de autorización** (no forma parte de esta intervención).
3. IMP02220 y `lot_flow_type` histórico: **intactos**.

## 15. Propuesta de commit (NO ejecutado)
```
feat(sv-rebaja): recorrido simplificado Guardar/Aplicar en la misma ventana (18.0.1.20.0)

- <header>: [Guardar] [Aplicar] [Volver]; opciones avanzadas en «Más opciones»
- action_apply permanece en la ventana y muestra apply_result (no abre el documento)
- mensajes según problema real (falta de cantidad vs. sin disponibilidad)
- tablas en sólo lectura tras aplicar
- tests SIMPLE-01..17 + CLIENT-01..03; test_arch_01 y test_ui_02 actualizados
```

**Sin commit · sin push · sin despliegue remoto · sin reparación histórica.**

