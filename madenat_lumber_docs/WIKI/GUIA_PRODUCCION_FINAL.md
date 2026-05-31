# Guía de Producción y Validación Final — MADENAT

**Estado:** ACTIVO
**Última actualización:** 2026-05-23
**Objetivo:** definir la secuencia mínima obligatoria antes de validar un cierre técnico o autorizar deploy.

---

## 1. Principio de despliegue

No existe deploy confiable sin instalación limpia, validación mínima suficiente y documentación sincronizada.
La ausencia de errores de sintaxis no basta; el módulo debe sostener coherencia entre código, vistas, tests, continuidad y decisión técnica. [file:7][file:5][file:4]

---

## 2. Qué debe estar resuelto antes de pensar en producción

### Requisitos técnicos
- el módulo debe actualizar sin fallar registry;
- no debe existir `Wrong @depends`;
- el naming de campos debe ser coherente entre código, vistas, tests y documentación;
- `length` debe mantenerse como fuente de verdad en metros. [file:7][file:5][file:4]

### Requisitos funcionales
- T01–T14 deben seguir firmes;
- T29–T32 deben estar ejecutadas o revalidadas según contexto;
- el flujo manual shipment → consolidation debe funcionar en UI;
- la trazabilidad operativa debe mantenerse. [file:5][file:7]

### Requisitos documentales
- `02_CONTINUIDAD.md` actualizado;
- `05_BACKLOG.md` priorizado;
- `03_TESTS.md` alineado;
- `04_DECISION_LOG.md` actualizado si cambió una regla;
- `06_CHECKLIST.md` coherente con el criterio real de cierre. [file:5][file:4][file:7]

---

## 3. Secuencia correcta antes de deploy

1. Confirmar el estado vigente en `02_CONTINUIDAD.md`. [file:5]
2. Revisar la tarea activa en `05_BACKLOG.md`.
3. Ejecutar grep de naming sensible si hubo cambios en largo/unidades:
   ```bash
   grep -RniE "lengthinputraw|lengthuom|_compute_lengthm" models wizard tests views
   ```
4. Limpiar caché técnica si corresponde.
5. Actualizar módulo en DB de prueba.
6. Confirmar carga limpia de vistas y registry.
7. Ejecutar pruebas base.
8. Ejecutar pruebas específicas del cambio.
9. Validar manualmente en UI el flujo afectado.
10. Recién entonces evaluar salida controlada.

---

## 4. Comandos de referencia

### Update de prueba
```bash
docker exec -it odoo18_app bash -lc "
odoo -u madenat_lumber_core -d madenattest \
--db_host=db --db_user=odoo --db_password=odoo \
--xmlrpc-port=8072 --test-enable --stop-after-init \
--log-level=test
"
```

### Búsqueda de naming sensible
```bash
grep -RniE "lengthinputraw|lengthuom|_compute_lengthm" models wizard tests views
```

### Limpieza básica de caché Python
```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

---

## 5. Validación funcional mínima obligatoria

### Flujo base
- recepción física y Gate 0 sin side effects;
- Gate 1 y staging sin side effects;
- Gate 2 sin side effects;
- Gate 3 como único write real. [file:7][file:4]

### Largo y unidades
- conversión `ft → m`;
- conversión `mm → m`;
- conversión `m → m`;
- quick-create de subproducto;
- consistencia entre `lengthinputraw`, `lengthuom` y `length`.

### Fase 6: OPERATIVA
- shipment en estado `delivered`;
- botón `Crear Consolidación` visible;
- ejecución correcta de la acción;
- creación de consolidación y líneas asociadas. [file:5]

---

## 6. Criterio de no deploy

No se debe desplegar si ocurre cualquiera de estas condiciones:

- el módulo no actualiza limpio;
- existe incoherencia documental relevante;
- T29–T32 no tienen evidencia suficiente cuando el cambio afecta largo/unidades;
- el flujo manual de consolidación no fue validado;
- el backlog y la continuidad no reflejan el estado real. [file:5][file:7][file:4]

---

## 7. Criterio de deploy controlado

Se puede considerar deploy controlado cuando se cumplen simultáneamente estas condiciones:

- instalación limpia;
- pruebas base firmes;
- pruebas específicas evidenciadas;
- validación UI satisfactoria;
- documentación canónica actualizada;
- punto de retoma claro en caso de rollback o seguimiento. [file:7][file:5]

---

## 8. Cierre documental posterior a validación

Después de validar o desplegar:

1. actualizar `02_CONTINUIDAD.md`;
2. actualizar `05_BACKLOG.md`;
3. actualizar `04_DECISION_LOG.md` si cambió una regla;
4. registrar el siguiente paso explícito;
5. dejar trazabilidad suficiente para que otro ingeniero retome sin reconstruir contexto. [file:5][file:4][file:7]

---

## 9. Regla final

Sin instalación limpia, no hay deploy.
Sin evidencia mínima suficiente, no hay cierre técnico.
Sin documentación alineada, no hay confianza operativa. [file:7][file:5][file:4]