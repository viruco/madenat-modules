# Informe — Cierre mínimo de validación de duplicados en la ingesta

**MADENAT — Odoo 18 CE** · 2026-10-07 · **Entrega AISLADA. NO desplegada.**
Base: `AUDIT_GUIA_DUPLICADOS_20261007/…` y `FIX_GUIA_DUP_20261007_164415/…`.
Construcción **incremental** sobre el parche previo (no reimplementación).

## 1. Qué se ajustó

| Ajuste | Cambio | Archivo |
|---|---|---|
| **A — identidad incompleta** | Si `partner_id` no se conoce, **no** se valida/bloquea como duplicado; se conserva la captura y se **revalida** al completar. | `madenat_guia_processing.py` (`_check_guide_identity_duplicate*`) |
| **B — simetría Recepción/Procesado** | El parámetro `cross_model` pasa a **default `False`** y se aplica igual en ambas rutas → una coincidencia de número entre flujos **no bloquea** en ningún sentido. | `reception_parser.py` (`_check_guide_duplicate`) |
| **C — homónimos** | Se añade **aviso no bloqueante** en el chatter (`mail.thread`, mecanismo existente) al detectar un homónimo; la validación efectiva permanece en servidor. | `madenat_guia_processing.py` (`_warn_guide_homonym`) |
| Detección sin bloquear | C1 acepta `raise_on_match=False` → devuelve `(modelo, registro)` en vez de lanzar. | `reception_parser.py` |
| Corrección documental | `test_02` del validador se alinea a `CANON/12 §5.2`. | `tests/test_duplicate_validation.py` |

Sin nuevos campos, modelos, ACL, locks, índices ni `sudo`. No se toca CANON.

## 2. Qué documento respalda cada comportamiento

| Comportamiento | Fuente vigente |
|---|---|
| Identidad de guía = `name` + `partner_id`; número informativo | `CANON/12 §2`, `§3.3`, `§5.2` |
| Homónimo entre flujos no bloquea | `CANON/12 §5.2`, `§6.2` |
| Captura incompleta permitida (draft) | `CANON/00 §4.3`; `CANON/12 §11.5` (bloqueo al salir a stock) |
| Corrección/relectura del propio documento | `CANON/00 §4.2`, `§4.3` |
| Cancelado conserva trazabilidad y sigue contando | `CANON/12 §11.7`; `CANON/00 §4.9` (Modo B) |
| Particularidades de Volúmenes | `CANON/12 §11.5–11.6`; `CANON/17 §1.4` |
| Advertir sin bloquear | `CANON/04 AD-88` (mixin `madenat.deviation.mixin`) |

**Conflicto documental resuelto:** la recomendación D1 de la auditoría (bloquear homónimos)
contradecía `CANON/12 §5.2`; se resolvió **corrigiendo el parche** (no bloquea; advierte),
sin cambiar la doctrina. Detalle en `MATRIZ_ALINEACION.md`.

## 3. Qué pruebas lo demostraron

- **Positivo (esta entrega):** `0 failed, 0 error(s) of 38 tests`.
- **Negativo (parche previo):** `1 failed, 5 error(s)` — exactamente las 6 pruebas que
  dependen de A/B/C (`test_02`, `test_06b`, `test_27`, `test_28`, `test_29`, `test_30`).
- Efectos verificados: **cabecera** y **líneas de staging**; **no** lotes/movimientos.
- Detalle en `RESULTADOS_PRUEBAS.md`; logs en `logs/`.

## 4. Qué sigue pendiente

1. **Cierre del riesgo `partner_id` nulo** (dos capturas homónimas e incompletas no se
   bloquean hasta completar el proveedor): requiere **propuesta separada** (índice único
   parcial) — *no implementado*.
2. **Concurrencia real:** no cubierta (el `search` previo es secuencial). Sin propuesta en
   esta entrega.
3. **AD-88 pasivo:** el aviso homónimo no exige motivo; queda a **ratificación** si se
   desea tipificarlo como desviación con motivo.
4. **Aviso en la ruta de Recepción:** simétrica en bloqueo (B) pero **sin** aviso chatter
   (fuera del alcance mínimo). A decidir si se añade.
5. **Cobertura de stock:** no ejecutada.

## 5. ¿Listo para solicitar aplicación?

**Sí, con límites.** El parche está probado en aislamiento con usuario operativo y sin
superusuario, con control negativo. Límites declarados: riesgo residual `partner_id` nulo,
concurrencia no cubierta y aviso no ratificado. **No** se despliega; requiere autorización
(ver `PLAN_APLICACION_REVERSION.md`).

---

## CIERRE (respuestas directas)

1. **Qué se ajustó:** A (la identidad incompleta ya no bloquea y se revalida al completar),
   B (simetría entre Recepción y Procesado: el número no bloquea entre flujos en ningún
   sentido), C (aviso no bloqueante de homónimo en el chatter). Además C1 ganó
   `raise_on_match` y default `cross_model=False`.
2. **Qué documento respalda cada comportamiento:** ver §2 (CANON/12 §2/§5.2/§6.2/§11.5–11.7,
   CANON/00 §4.2/§4.3/§4.9, CANON/17, CANON/04 AD-88). Conflicto D1→§5.2 resuelto.
3. **Qué pruebas lo demostraron:** 38 tests (30 nuevos + 8 regresión) `0 failed`; control
   negativo con el parche previo falla exactamente en las 6 dependientes de A/B/C.
4. **Qué sigue pendiente:** riesgo `partner_id` nulo (propuesta separada), concurrencia, la
   ratificación del aviso pasivo (AD-88) y el aviso en la ruta de Recepción.
5. **¿Listo para aplicar?** Sí, bajo los límites de §4/§5, y **sólo con autorización** de
   aplicación (árbol activo + `-u` + reinicio). **Esta entrega NO autoriza el despliegue.**
