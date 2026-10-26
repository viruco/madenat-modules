# CONTRATO DE APLICACIÓN (REBAJA A SV) — PROPUESTA PARA APROBACIÓN

**Fecha:** 2026-10-11 · **Base:** `madenat_test` · **Módulo:** `madenat_lumber_logistics` **18.0.1.16.0**
**Documentación canónica:** `madenat_lumber_docs/CANON/` (`19` §19.23, `02` §17.16.21, `03` §24–25).
**Estado:** **POLÍTICA APROBADA POR MAURICIO (2026-10-11) e IMPLEMENTADA** en
`madenat_lumber_logistics` **18.0.1.17.0**. **Aceptación operativa (navegador) pendiente.**

Rama `feat/guia-correccion-documental-preservada-20261002`, HEAD `b1d2d19`. Correcciones y pruebas de
18.0.1.16.0 **preservadas** (AUD-ETQ-01/02/03/04/06/07; `test_sv_rebaja_blindaje.py`,
`test_sv_rebaja_cierre.py`, `security/madenat_sv_imputation_rules.xml`). Sin commit/push/despliegue.

---

## 1. Propuesta de política (APROBADA por Mauricio el 2026-10-11)

> **En la rebaja a SV, «Aplicar» requiere al menos un reparto válido con cantidad positiva hacia un SV
> autorizado. Sin reparto, el documento sólo puede permanecer en un estado no aplicado. El reparto
> parcial mantiene la política vigente de compromiso nominal, mostrando expresamente la cantidad que
> queda comprometida sin repartir.**

**No se interpreta el silencio como autorización.** Si se requiere una modalidad de compromiso **sin
destino**, se define por separado (finalidad, estado, reservas, compleción posterior, cancelación,
trazabilidad y diferencia respecto a una rebaja aplicada a SV); **no** como excepción por motivo genérico.

## 2. Diseño de implementación (APLICADO en 18.0.1.17.0)

**Punto único de validación (backend, no sólo botón):** `madenat.sv.imputation._i2_validate_payload()`,
que `action_apply` ejecuta **antes** de adquirir locks, revalidar techos y escribir estado. Por tanto
cubre interfaz, ORM y RPC, y **no** consume capacidad ni crea documento aplicado si falla.

Regla a añadir (borrador, sujeto a aprobación):

```python
# Aplicar exige ≥ 1 reparto con cantidad positiva hacia un SV autorizado.
positivos = self.sv_line_ids.filtered(
    lambda s: float_compare(s.imputed_volume_m3, 0.0,
                            precision_rounding=I2_VOLUME_PRECISION) > 0
    and s.sv_lot_id and s.sv_lot_id.lot_flow_type == 'volume')
if not positivos:
    raise UserError(_(
        'No se puede aplicar la rebaja: asigna una cantidad positiva a un SV. '
        'Puedes guardar el documento sin aplicarlo.'))
```

Se conserva **sin cambios**: `action_prepare`/`action_pending` (permiten trabajo incompleto),
`_check_single_work_per_guia`, inmutabilidad del aplicado, reversa con motivo, idempotencia, locks,
techo duro, reparto parcial/multi-SV y ausencia de efectos físicos. Revalidación completa en la
transición: reparto válido · cantidad positiva · destino autorizado (`lot_flow_type='volume'`) ·
coherencia documento/etiquetas/repartos · disponibilidad actual (techo duro) · estado · compañía y permisos.
**Una fila de volumen cero no satisface el requisito** (además del `constraint` ya existente).

## 3. Mensaje operativo

Sin reparto positivo, el rechazo dice **qué falta y cómo continuar**:

> «No se puede aplicar la rebaja: asigna una cantidad positiva a un SV. Puedes guardar el documento sin
> aplicarlo.»

No es una excepción técnica y **no** aplica nada automáticamente. La revisión previa muestra, sin
equipararlos: **nominal comprometido** ≠ **cantidad repartida a SV** ≠ **pendiente de reparto** ≠
**efecto por saldo de SV** (campos existentes: `nominal_total_m3`, `imputed_total_m3`,
`etiqueta_pendiente_m3`, `sv_saldo_documental_m3`).

## 4. Pruebas del contrato (activas)

`POL-01` sin filas → rechazo · `POL-02` filas a cero → rechazo · `POL-03` reparto positivo válido →
permitido · `POL-04` parcial → pendiente comprometido explícito · `POL-05` guardar/reabrir incompleto →
conserva sin aplicar · `POL-06` ORM/RPC directo sin reparto → mismo rechazo · `POL-07` repetición tras
rechazo → sin documento parcial ni consumo extra · `POL-08` aplicar→revertir→reasignar→aplicar con
balances e historia. Borrador en `evidence/POL_contrato_tests_draft.py` (no incluido en `tests/__init__.py`
para no dejar la suite en rojo antes de la aprobación).

## 5. IMP02220 — dry-run de alternativas (NO ejecutado)

Ver `evidence/imp02220_dryrun.md`. Registro exigido:
**«Aplicado bajo comportamiento anterior; nominal comprometido sin reparto SV; pendiente de decisión de
regularización»**. **No** se modifica el documento ni `lot_flow_type`.

## 6. Precisión sobre concurrencia (Q1–Q3)

Resultados de la sonda `AUDIT_REBAJA_ETIQUETAS_20261011/evidence/concurrency_probe.py` (cursores
independientes + `threading.Barrier`), descritos con exactitud:

- **Q1 (doble aplicación sobre la misma capacidad):** **una** operación obtiene el recurso y aplica; la
  otra recibe un **rechazo controlado** (`UserError`: «Otra operación está modificando la misma etiqueta de
  retorno…»). Documentos aplicados: **1/2**; Σ activo = 10.000 = nominal ⇒ **sin sobreconsumo**.
- **Q2 (doble reversa sobre el mismo aplicado):** **integridad preservada**: estado final `reversed`,
  **1** auditoría de reversa, **0** etiquetas aún aplicadas ⇒ **sin doble restitución**. La 2.ª transacción
  termina con `SerializationFailure` de PostgreSQL («could not serialize access due to concurrent update»).
- **Q3 (aplicar ∥ cancelar reserva):** la cancelación procede; la aplicación concurrente es **rechazada
  por el techo duro** («…acumula 20.000 m³… frente a su volumen nominal… 10.000»). Σ activo ≤ nominal ⇒
  **sin sobreconsumo**.

**Límite específico declarado (Q2, vía normal de ejecución):** la prueba se ejecutó por **ORM en cursores
independientes**, no por la interfaz. Por tanto **no está verificado** si la transacción perdedora de Q2
**reintenta automáticamente** o si el usuario **recibe un error y debe reintentar** en la ruta normal de
pantalla. No se confunde «no hubo doble restitución» con «experiencia de usuario validada»: queda como
**límite**, a comprobar en el guion de navegador.

**Seguridad y concurrencia conservadas:** POL‑01..08 no alteran los advisory locks (`_i2_lock_resources`),
el techo duro ni la atomicidad; la nueva validación se ejecuta **antes** de los locks ⇒ un rechazo no deja
documento parcial, ni consumo, ni reserva adicional.

## 7. Aceptación en navegador

Guion en `docs/GUION_NAVEGADOR_CONTRATO.md` (A–I). **Sin navegador en este entorno** ⇒ aceptación
operativa **pendiente de Mauricio**; no se sustituye por XML/ORM/SQL.

## 8. Dictamen

**CONTRATO IMPLEMENTADO Y PROBADO; ACEPTACIÓN OPERATIVA PENDIENTE.** Política **aprobada por Mauricio el
2026-10-11**; validación backend en `_i2_validate_payload`; POL‑01..08 en verde; regresión con las mismas
fallas preexistentes. `NO_SV_CANDIDATE` pasa a **informativo**. IMP02220 permanece **sin reparar**. Sólo
tras la comprobación del usuario (guion A–I): «Flujo aceptado por Mauricio», con alcance y fecha.
