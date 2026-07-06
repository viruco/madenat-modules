## MADENAT — Protocolo Canónico de Trabajo con IA

**Versión documental:** 7.3.0
**Fecha de actualización:** 2026-07-01
**Estado:** ACTIVO — Actualizado post-auditoría documental y limpieza CANON
**Propósito:** permitir que cualquier IA entienda el proyecto, el estado real y las reglas de trabajo sin reconstruir contexto desde cero en cada sesión.

---

## 1. Contexto del proyecto

**Proyecto:** MADENAT Lumber Core
**Módulo principal:** `madenat_lumber_core`
**Plataforma:** Odoo 18 CE
**Entorno:** Docker en WSL (`odoo18_app`, `db` / `odoo18_db`)
**Repositorio:** `~/dev-stack/odoo/odoo-18-ce/custom_addons/`
**Documentación canónica:** `madenat_lumber_docs/`

**Propósito del módulo:** gestionar el flujo completo de recepción de madera desde documento origen hasta `stock.lot`, con trazabilidad matemática, validación por gates y persistencia controlada a inventario.

**Cadena funcional:**
```text
madenat_lumber_shipping_core
          ↓
  madenat_lumber_core
          ↓
madenat_lumber_logistics / madenat_lumber_billing
```

---

## 2. Estado real del proyecto (2026-07-01)

### Resuelto
- Gates 0 a 3 + GB-1 implementados y documentados en `00_ARQUITECTURA.md`.
- Suite T01–T14 validada como núcleo estable.
- Triple capa operativa (visual / física / nominal) como regla de negocio.
- Parser, workflow, servicio de stock, helpers y mixins desacoplados del monolito.
- Bug crítico de naming resuelto (`length_input_raw` / `lengthuom`).
- Módulo actualiza sin error de registry (86 módulos cargados en 4.71s, 0 errores).
- Fase 6 manual: `action_create_consolidation_from_shipment` implementada.
- AD-26 ejecutado: 33 `.bak` → LEGADO, 0 residuos en módulos productivos.
- AD-37 ejecutado: autoridad documental de shipping_core consolidada en CANON.
- AD-38 ejecutado: desalineación `wood_cost_usd` Float vs Monetary documentada.
- CHANGELOG cerrado: `[Unreleased]` → `[18.0.5.4.0] - 2026-07-01`.
- CANON auditado y limpiado (2026-07-01): 6 docs archivados en LEGADO, 9 vigentes, 2 derivados.
- Fases A (Monetaria) y C (Tests) parcialmente completadas.

### Abierto / pendiente
- T29–T32 pendientes de ejecución formal (tests automatizados existen, falta evidencia en staging).
- Validación funcional extremo a extremo de Fase 6 en UI.
- Constraint `stock_lot_check_cost_positive` aún abierto.
- Monolito parcial en `lumber_reception.py` (refactor futuro — Fase 4 del backlog).
- Separación final de `LumberReceptionLine` a archivo propio.
- Fases C (CHANGELOGs), D (scripts), E (staging) pendientes para cerrar ciclo pre-deploy.
- `deduction_factor` Blank (0.0625) pendiente de confirmación con Cristhian (C3).

---

## 3. Reglas técnicas no negociables

- Odoo 18 CE: usar `<list>` en vistas de lista, nunca `<tree>`.
- Sin SQL raw en producción.
- Sin fallback silencioso para tipo de cambio.
- Sin writes en Gate 0, Gate 1 ni Gate 2. Solo Gate 3 escribe inventario real.
- `length` es la fuente de verdad en metros. Nunca calcular sobre `lengthinputraw`.
- `length_input_raw` preserva el valor del operador.
- `lengthuom` define la unidad de entrada (`m`, `mm`, `ft`).
- Conversión: `mm → * 0.001`, `ft → * 0.3048`, `m → * 1.0`.
- El naming debe ser coherente entre Python, XML, tests y documentación. Cualquier discrepancia es bug crítico (AD-17).
- El módulo debe actualizar sin fallar registry antes de cualquier deploy.

---

## 4. Documentación canónica activa

| Archivo | Propósito |
|---|---|
| `INDICE_DOCUMENTACION.md` | Mapa maestro de todos los documentos. Único punto de entrada. |
| `00_ARQUITECTURA.md` | Arquitectura, modelos, gates, campos, restricciones |
| `02_CONTINUIDAD.md` | Checkpoint técnico vivo. Estado actual, riesgos, punto de retoma |
| `03_TESTS.md` | Matriz de validación funcional y técnica (T01–T33 + suites automatizadas) |
| `04_DECISION_LOG.md` | Decisiones de arquitectura, naming, cálculo y operación (AD-01 a AD-38) |
| `05_BACKLOG.md` | Backlog canónico y priorizado por fases |
| `05_AUDITORIA_XML_IDS.md` | Auditoría de XML IDs — R1 Stock Detail |
| `07_TRABAJO_CON_IA.md` | Este archivo. Protocolo de trabajo con IA |
| `08_COSTEO.md` | Flujo canónico de costeo end-to-end |
| `11_FASE_E_VALIDACION.md` | Runbook operativo, CI pipeline (derivado vigente) |
| `12_FLUJOS_INGESTA.md` | Flujos de ingesta y discriminación operativa |
| `15_DIAGNOSTICO_NAVEGACION_ACTUAL.md` | Diagnóstico de navegación actual (derivado vigente) |

**Documentos archivados en LEGADO (2026-07-01):**
`01_FLUJO_PACKING.md`, `06_CHECKLIST.md`, `09_FASE_DOCUMENTAL_MAESTRA.md`, `10_AUDITORIA_MONETARIA_FASE_A.md`, `12_ARQUITECTURA_OPERATIVA_PERFILES.md`, `13_ARQUITECTURA_TECNICA_IMPLEMENTACION.md`, `14_GUIA_EJECUCION_INCREMENTAL.md`

**Documentos WIKI (no canónicos, auxiliares):**
`WIKI/00_INDICE.md`, `WIKI/QUICK_START.md`, `WIKI/GUIA_PRODUCCION_FINAL.md`, `WIKI/HOJA_RUTA_EJECUTIVA.md`

**Criterio de verdad ante contradicción:**
1. Documento canónico del tema.
2. `04_DECISION_LOG.md`.
3. `02_CONTINUIDAD.md`.
4. Histórico solo como evidencia contextual.

---

## 5. Principio de trabajo con IA

No reexplicar lo que no cambió.
Sí declarar siempre el contexto mínimo suficiente para que la IA trabaje sobre base real y no sobre suposiciones.

---

## 6. Jerarquía de contexto por sesión

| Nivel | Contenido | Cuándo se envía |
|---|---|---|
| 1 | Arquitectura estable | Solo si cambió |
| 2 | Checkpoint operativo (`02_CONTINUIDAD.md`) | En cada sesión |
| 3 | Caso puntual (error, tarea, cambio) | Cuando aplica |
| 4 | Feedback estructurado | Después de cada iteración |

---

## 7. Cápsula mínima de sesión

```md
## SESIÓN MADENAT

### Identidad del proyecto
- Módulo: madenat_lumber_core
- Plataforma: Odoo 18 CE
- Entorno: Docker en WSL (odoo18_app / db)
- Documentación: madenat_lumber_docs/ — canónica y reorganizada al 2026-05-23

### Contexto activo
- Fase:
- Task:
- Objetivo:
- Prioridad:

### Ambiente
- Base de datos:
- Rama / commit:
- Contenedores activos:
- Módulo a tocar:

### Alcance
- Tocar:
- No tocar:

### Evidencia disponible
- Caso:
- Hallazgo actual:
- Riesgo activo:

### Tipo de ayuda necesaria
[ ] analizar  [ ] proponer  [ ] actualizar  [ ] paso a paso  [ ] consolidar

### Salida esperada
[ ] explicación  [ ] diff  [ ] archivos completos  [ ] checklist  [ ] próximos pasos
```

---

## 8. Regla de actualización por archivo

| Si cambia esto | Actualizar estos archivos |
|---|---|
| Estado o foco actual | `02_CONTINUIDAD.md` + `05_BACKLOG.md` |
| Regla técnica o criterio | `04_DECISION_LOG.md` + `00_ARQUITECTURA.md` |
| Flujo operativo | `12_FLUJOS_INGESTA.md` + `02_CONTINUIDAD.md` |
| Naming de campos | `00_ARQUITECTURA.md` + `03_TESTS.md` + `04_DECISION_LOG.md` + `02_CONTINUIDAD.md` |
| Se cierra una task | `05_BACKLOG.md` + `02_CONTINUIDAD.md` |
| Riesgo nuevo | `02_CONTINUIDAD.md` + `05_BACKLOG.md` |
| Criterio de validación o deploy | `11_FASE_E_VALIDACION.md` + `WIKI/GUIA_PRODUCCION_FINAL.md` |
| Forma de trabajar con IA | Este archivo |

---

## 9. Regla especial para bugs de naming

Si el bug involucra diferencia entre nombre Python, nombre XML, nombre en tests o nombre documentado:

No basta con corregir código. También hay que sincronizar:

- `00_ARQUITECTURA.md`
- `02_CONTINUIDAD.md`
- `03_TESTS.md`
- `04_DECISION_LOG.md`
- `05_BACKLOG.md`
- `07_TRABAJO_CON_IA.md`
- `INDICE_DOCUMENTACION.md`

---

## 10. Regla de ingeniería aplicada a IA

Toda interacción debe seguir este orden:

1. Investigar (grep, logs, estructura, documentación).
2. Mapear dependencias (quién usa qué).
3. Entender el problema real, no solo el síntoma.
4. Proponer solución mínima.
5. Validar impacto (¿rompe algo más?).
6. Documentar cambios.
7. Solo entonces considerar deploy o cierre.

La IA no debe proponer cambios sin haber pasado por el paso 1 y 2 primero.

---

## 11. Modos de salida válidos

- Explicación primero, luego propuesta.
- Diff limpio y luego archivos completos.
- Archivos completos listos para pegar con `cat <<'EOF'`.
- Paso a paso numerado y ejecutable.
- Consolidación documental completa alineada con canónico.

---

## 12. Criterio de éxito de sesión

Una sesión se considera bien ejecutada cuando:

- el foco quedó claro desde el inicio;
- los cambios aterrizaron en los archivos correctos;
- el estado del proyecto quedó consistente;
- la documentación cuenta la misma historia que el código;
- el siguiente punto de retoma quedó explícito.

---

## 13. Criterio de no avance

No se considera cerrado un cambio mientras:

- el código cambió y la documentación no lo refleja;
- existe incoherencia de naming entre código, vistas, tests y documentación;
- el backlog no refleja la prioridad real;
- la continuidad no tiene un punto de retoma claro;
- el módulo no instala limpio.

---

## 14. Comandos de referencia rápida

### Update de módulo
```bash
docker exec -it odoo18_app bash -lc "
odoo -u madenat_lumber_core -d madenattest --db_host=db --db_user=odoo --db_password=odoo --xmlrpc-port=8072 --test-enable --stop-after-init --log-level=test
"
```

### Grep de naming sensible
```bash
### Validación de naming: Confirmar consistencia en models, wizard, tests y views.
```

### Limpieza de caché Python
```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```
