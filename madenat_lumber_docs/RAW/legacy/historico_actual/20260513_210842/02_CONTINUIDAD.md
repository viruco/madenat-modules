# MADENAT — Estado de Continuidad Técnica

**Versión documental:** 5.0.0  
**Fecha de actualización:** 2026-05-13  
**Estado:** ACTIVO — Incidencia crítica actual en instalación por `@depends` inconsistente

---

## 1. Propósito

Este documento es el checkpoint técnico vivo del proyecto.  
Debe permitir retomar el trabajo sin reconstruir el contexto desde cero.

---

## 2. Estado actual resumido

### Infraestructura
- Módulo: `madenat_lumber_core`
- Target: Odoo 18 CE
- Ambiente usual: Docker (`odoo18_app`, `db` / `odoo18_db` según stack)
- Arquitectura: modular parcial

### Estado funcional consolidado
- Gates 0 a 3 definidos documentalmente
- Suite T01–T14 consolidada en documentación
- Triple capa operativa como regla de negocio
- Servicio de persistencia y parser ya desacoplados

### Estado real actual
La actualización reciente de largo por unidad de ingreso dejó documentación y vistas alineadas hacia:
- `length_input_raw`
- `length_uom`
- `length`

pero el código aún presenta al menos una dependencia antigua a `lengthinputraw`, generando error de instalación del módulo en la construcción del registry.

---

## 3. Hallazgo crítico vigente

### Incidente activo
Durante actualización/instalación del módulo se obtiene:

```text
ValueError: Wrong @depends on '_compute_lengthm'
Dependency field 'lengthinputraw' not found in model lumber.reception.line
```

### Interpretación
No es un problema de la vista actual.  
Es un problema de coherencia entre:
- definición de campo,
- compute method,
- decorador `@depends`,
- y nombres documentados tras el cambio del 2026-05-13.

### Estado
- Documentación: alineada a `length_input_raw`
- Vista: alineada a `length_input_raw`
- Código Python: inconsistencia viva
- Instalación de módulo: bloqueada

---

## 4. Cambios documentados 2026-05-13

## Cambio A — Wizard mass update
- Se incorpora vista XML del wizard de actualización masiva.
- `subproduct_id` opera con `quick_create`.
- Debe convivir con restricciones comerciales del flujo.

## Cambio B — Largo con unidad de ingreso
- Campo nuevo: `length_uom`
- Campo nuevo: `length_input_raw`
- `length` pasa a consolidarse como valor normalizado en metros
- Factores documentados:
  - `mm = * 0.001`
  - `ft = * 0.3048`
  - `m = * 1.0`

## Cambio C — T29 a T32
Se reservan documentalmente los siguientes escenarios:
- T29: ft → m
- T30: mm → m
- T31: m → m
- T32: quick-create subproducto

**Nota:** estos escenarios están definidos documentalmente, pero no deben marcarse como cerrados mientras el bug de instalación siga abierto.

---

## 5. Estado de pruebas

### Pruebas documentadas consolidadas
- T01–T14: base estable de negocio
- T15–T28: saneamiento y blindaje documental ya registrados en matriz histórica

### Pruebas bloqueadas o no cerradas
- T29–T32 dependen de resolver primero la inconsistencia del `@depends`

---

## 6. Prioridades inmediatas

### Prioridad 1 — Reparar instalación
Buscar y corregir todas las referencias antiguas:
- `lengthinputraw`
- `lengthuom`
- y cualquier compute asociado a `_compute_lengthm`

### Prioridad 2 — Revalidar upgrade
Ejecutar:
- limpieza de `__pycache__` dentro del addon
- update del módulo en DB de prueba
- validación de carga de vistas y registry

### Prioridad 3 — Cerrar documentalmente T29–T32
Solo después de resolver la instalación:
- ajustar matriz de tests
- cerrar continuidad
- actualizar checklist de finalización

---

## 7. Riesgos activos

| Riesgo | Severidad | Estado |
|---|---|---|
| `@depends` roto para largo | Crítica | Abierto |
| Constraint `stock_lot_check_cost_positive` | Alta | Abierto |
| Modelo financiero ausente | Alta | Abierto |
| Warnings XML menores | Media | Abierto |
| Monolito parcial en `lumber_reception.py` | Media | Abierto |

---

## 8. Qué tocar y qué no tocar

### Sí tocar
- documentación canónica
- compute y depends de largo
- tests de largo
- continuidad y decisión técnica

### No tocar aún
- arquitectura global congelada
- refactor grande de separación de archivos
- Fase 6 financiera antes de estabilizar instalación

---

## 9. Punto de retoma recomendado

1. Hacer grep de `lengthinputraw`, `length_input_raw`, `lengthuom`, `length_uom`, `_compute_lengthm`.
2. Corregir compute y decoradores.
3. Volver a correr upgrade con `-u madenat_lumber_core`.
4. Si instala, ejecutar T29–T32.
5. Solo entonces retomar backlog financiero.

---

## 10. Regla de oro de continuidad

Si se modifica:
- naming de campos,
- unidad de largo,
- computes,
- o contratos de Gate 2/Gate 3,

este documento debe actualizarse antes del siguiente checkpoint.
