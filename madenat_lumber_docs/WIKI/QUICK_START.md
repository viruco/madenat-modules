# Quick Start — MADENAT

**Estado:** ACTIVO
**Última actualización:** 2026-05-23
**Objetivo:** permitir retomar trabajo útil en pocos minutos sin perder contexto ni abrir frentes equivocados.

---

## 1. Lectura mínima obligatoria

Antes de tocar código o documentación, leer en este orden:

1. `INDICE_DOCUMENTACION.md`
2. `02_CONTINUIDAD.md`
3. `05_BACKLOG.md`
4. `03_TESTS.md`
5. `06_CHECKLIST.md`

Esta secuencia entrega contexto, estado real, prioridad activa, validación esperada y criterio operativo de sesión.

---

## 2. Estado actual en una línea

La base funcional del módulo está estable, el incidente de `Wrong @depends` quedó resuelto y el foco vigente es cerrar evidencia formal de largo/unidades (`T29–T32`) y validar extremo a extremo la Fase 6 manual desde shipment hacia consolidación.

---

## 3. Qué hacer primero

1. Confirmar la tarea activa en `05_BACKLOG.md`.
2. Revisar en `02_CONTINUIDAD.md` el punto exacto de retoma.
3. Verificar consistencia de naming en el código real antes de proceder.
4. Confirmar que documentación, vistas, tests y código usan naming consistente (`lengthinputraw`, `lengthuom`).
5. Ejecutar o preparar la validación pendiente antes de abrir un frente nuevo.

---

## 4. Foco técnico recomendado hoy

### Prioridad 1
Cerrar evidencia reproducible de T29–T32:
- ft → m
- mm → m
- m → m
- quick-create de subproducto

### Prioridad 2
Validar funcionalmente la Fase 6 manual:
- shipment en `delivered`
- botón `Crear Consolidación`
- creación de `lumber.billing.consolidation`
- creación de `lumber.billing.consolidation.line`

### Prioridad 3
Actualizar continuidad, backlog, tests y decision log si el estado real cambió.

---

## 5. Qué no hacer todavía

- No abrir refactor grande del monolito.
- No automatizar más billing antes de validar el flujo manual.
- No crear documentación paralela para temas que ya tienen dueño canónico.
- No cerrar features solo porque compilan; deben quedar evidenciados.

---

## 6. Regla de trabajo

Cada cambio debe seguir esta secuencia:

1. Investigar.
2. Mapear dependencias.
3. Entender el problema real.
4. Aplicar cambio mínimo.
5. Validar impacto.
6. Documentar.
7. Recién después considerar deploy.

---

## 7. Cierre mínimo de sesión

Antes de terminar:

- actualizar `02_CONTINUIDAD.md` si cambió el estado real;
- actualizar `05_BACKLOG.md` si cambió la prioridad;
- actualizar `04_DECISION_LOG.md` si cambió una regla;
- dejar próximos 3 pasos explícitos;
- dejar punto exacto de retoma.