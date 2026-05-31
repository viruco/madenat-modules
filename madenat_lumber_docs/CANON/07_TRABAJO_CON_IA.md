## MADENAT — Protocolo Canónico de Trabajo con IA

**Versión documental:** 7.1.0
**Fecha de actualización:** 2026-05-28
**Estado:** ACTIVO
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

## 2. Estado real del proyecto (2026-05-23)

### Resuelto
- Gates 0 a 3 implementados y documentados.
- Suite T01–T14 validada como núcleo estable.
- Triple capa operativa (visual / física / nominal) como regla de negocio.
- Parser, workflow, servicio de stock, helpers y mixins desacoplados del monolito.
- Bug crítico de naming resuelto (`lengthinputraw` / `lengthuom`).
- Módulo actualiza sin error de registry (`update --stop-after-init` cargó 85 módulos sin errores críticos).
- Fase 6 manual: `action_create_consolidation_from_shipment` implementada y cargando correctamente.
- Botón `💰 Crear Consolidación` visible en shipment cuando `state == 'delivered'`.
- UI Estandarizada: Alerts con `role="alert"` y Chatter corregido en `shipping_booking_views.xml`.

### Abierto / pendiente
- T29–T32 pendientes de ejecución formal (ft→m, mm→m, m→m, quick-create subproducto).
- Validación funcional extremo a extremo de Fase 6 en UI.
- Constraint `stock_lot_check_cost_positive` aún abierto.
- Monolito parcial en `lumber_reception.py` (refactor futuro).
- Separación final de `LumberReceptionLine` a archivo propio.

---

## 3. Reglas técnicas no negociables

- Odoo 18 CE: usar `<list>` en vistas de lista, nunca `<tree>`.
- Sin SQL raw en producción.
- Sin fallback silencioso para tipo de cambio.
- Sin writes en Gate 0, Gate 1 ni Gate 2. Solo Gate 3 escribe inventario real.
- `length` es la fuente de verdad en metros. Nunca calcular sobre `lengthinputraw`.
- `lengthinputraw` preserva el valor del operador.
- `lengthuom` define la unidad de entrada (`m`, `mm`, `ft`).
- Conversión: `mm → * 0.001`, `ft → * 0.3048`, `m → * 1.0`.
- El naming debe ser coherente entre Python, XML, tests y documentación. Cualquier discrepancia es bug crítico (AD-17).
- El módulo debe actualizar sin fallar registry antes de cualquier deploy.

---

## 4. Documentación canónica activa

| Archivo | Propósito |
|---|---|
| `INDICE_DOCUMENTACION.md` | Mapa oficial de todos los documentos |
| `00_ARQUITECTURA.md` | Arquitectura, modelos, gates, campos, restricciones |
| `01_FLUJO_PACKING.md` | Flujo funcional de packing y estados |
| `02_CONTINUIDAD.md` | Checkpoint técnico vivo. Estado actual, riesgos, punto de retoma |
| `03_TESTS.md` | Matriz de validación funcional y técnica |
| `04_DECISION_LOG.md` | Decisiones de arquitectura, naming, cálculo y operación |
| `05_BACKLOG.md` | Backlog canónico y priorizado por fases |
| `06_CHECKLIST.md` | Checklist operativo de sesión, validación y cierre |
| `07_TRABAJO_CON_IA.md` | Este archivo. Protocolo de trabajo con IA |
| `GUIA_PRODUCCION_FINAL.md` | Guía de validación y criterio de deploy |
| `HOJA_RUTA_EJECUTIVA.md` | Vista ejecutiva de estado, foco y prioridades |
| `QUICK_START.md` | Onboarding rápido para retomar trabajo |

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
| Flujo operativo | `01_FLUJO_PACKING.md` + `02_CONTINUIDAD.md` |
| Naming de campos | `00_ARQUITECTURA.md` + `03_TESTS.md` + `04_DECISION_LOG.md` + `02_CONTINUIDAD.md` |
| Se cierra una task | `05_BACKLOG.md` + `02_CONTINUIDAD.md` |
| Riesgo nuevo | `02_CONTINUIDAD.md` + `05_BACKLOG.md` |
| Criterio de validación o deploy | `06_CHECKLIST.md` + `GUIA_PRODUCCION_FINAL.md` |
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
