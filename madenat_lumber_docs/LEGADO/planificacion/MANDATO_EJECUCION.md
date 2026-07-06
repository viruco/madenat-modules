# MANDATO DE EJECUCIÓN — MADENAT Lumber
## Control operativo del plan de depuración

**Fecha:** 2026-06-05
**Entorno:** DEV (madenat_test)

---

## REGLA DE EJECUCIÓN

> **Lo no bloqueado se hace ya. Lo bloqueado no se fuerza. Todo avance deja evidencia.**

No se documenta más. Se ejecuta.

---

## 1. CASCADA DOCUMENTAL COMO SISTEMA DE CONTROL

Cada documento tiene una sola función. Se consulta solo cuando se necesita.

| Documento | Cuándo se usa |
|-----------|---------------|
| `PLAN_DEPURACION_PRIORIZADO.md` | Para entender **por qué** una brecha es P1 y no P3. No se lee en el día a día |
| `PLAN_ACCION_EJECUTABLE.md` | Para buscar el **script exacto** de una acción. Es la referencia técnica |
| `GUIA_OPERATIVA_IMPLEMENTACION.md` | Para seguir el **paso a paso** de una acción concreta. Incluye troubleshooting |
| `EJECUCION_FASE0.md` | Para saber **qué toca hacer hoy** y qué está bloqueado. Es el tablero diario |
| `CIERRE_DF01_GUIA_REUNION.md` | Para **la reunión con negocio**. Se usa una vez y se archiva |

**Regla:** si un documento no se está usando para ejecutar, es ruido. Fuera.

---

## 2. TRABAJO NO BLOQUEADO — EJECUTAR YA

Estas acciones no dependen de nadie. Se ejecutan en orden de prioridad por impacto:

| # | Acción | Esfuerzo | Archivo | Evidencia de cierre |
|---|--------|----------|---------|---------------------|
| 1 | A-13 — Verificar seed `lumber.export.formula` | 0.5h | SQL | 3 registros `active=t` |
| 2 | A-17 — Hardcodes `25.4` → `MM_PER_INCH` | 1h | 3 archivos `.py` | grep muestra solo definición en `utils_uom.py` |
| 3 | A-09 — `account_id` en `stock.lot.cost.line` | 1.5h | `stock_lot_cost_line.py` + vista | Columna existe en BD, campo visible en UI |
| 4 | A-19 — Tests `madenat_guia_processing` | 12h | Nuevo `test_guia_processing.py` | ≥ 6 tests PASS (mínimo viable) |
| 5 | A-11 — Verificar `vol_shipment_m3` | 3h | SQL diagnóstico | Query con `vol_shipment_m3 > 0` o documento de pendencia |

**A-19 corre en paralelo completo.** Asignar a un developer independiente.

Cada acción se cierra cuando su evidencia está registrada. Sin evidencia, no está cerrada.

---

## 3. DF-01 — LA PRIORIDAD FUNCIONAL

**DF-01 es la única decisión que bloquea la Fase 1 (6 acciones, 6h, primer `account.move`).**

Cerrarla requiere una reunión de 30 minutos con negocio. El documento `CIERRE_DF01_GUIA_REUNION.md` contiene:

- Las 3 opciones con matriz de comparación
- 5 preguntas concretas para negocio
- Árbol de decisión
- Plantilla de cierre lista para copiar en CANON

**Si negocio no responde en 48h:** el equipo adopta Opción A (costo desde `purchase.order`) como default técnico temporal, documentado en `CANON/08_COSTEO.md` con vigencia de 2 semanas. Esto desbloquea la Fase 1 sin esperar.

Evidencia de cierre de DF-01: entrada en `CANON/04_DECISION_LOG.md` con decisión, responsable y fecha.

---

## 4. CHECKPOINTS — PUERTAS DE TRANSICIÓN

No se cruza una fase sin evidencia. Cada checkpoint es binario: abierto o cerrado.

| Checkpoint | Condición | Desbloquea |
|------------|-----------|------------|
| **CP-0.1** | A-13 cerrado | — |
| **CP-0.2** | A-17 cerrado | — |
| **CP-0.3** | A-09 cerrado | — |
| **CP-0.4** | A-19 ≥ 6 tests PASS (o avance documentado) | — |
| **CP-0.5** | A-11 cerrado o documentado como pendiente | — |
| **CP-1** | DF-01 documentada en CANON | **Fase 1 completa** |
| **CP-4** | `account.move` posted desde landed cost | **Hito H1 alcanzado** |

**Lo que detiene el avance:**
- Cualquier checkpoint sin evidencia → no se avanza.
- Tests rotos por A-17 → se corrigen antes de continuar.
- `account.move` no se genera en A-07 → se revisa configuración contable, no se fuerza.

---

## 5. CONCLUSIÓN

La documentación está completa. El diagnóstico está hecho. Las brechas están priorizadas. Los scripts están escritos.

**Lo único que falta es ejecutar.**

El equipo trabaja así:
1. Cada día se revisa `EJECUCION_FASE0.md` para saber qué toca.
2. Cada acción se ejecuta con el script de `GUIA_OPERATIVA_IMPLEMENTACION.md`.
3. Cada cierre se registra con su evidencia.
4. DF-01 se resuelve con negocio usando `CIERRE_DF01_GUIA_REUNION.md`.
5. Cuando CP-1 se cierra, Fase 1 arranca y en ~6h se genera el primer `account.move`.

**Frase de ejecución del proyecto:**

> *Evidencia sobre intención. Avance sobre documentación. Cierre sobre discusión.*