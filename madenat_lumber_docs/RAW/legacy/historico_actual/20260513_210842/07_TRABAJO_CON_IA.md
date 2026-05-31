# MADENAT — Protocolo de Trabajo con IA

**Versión documental:** 5.0.0  
**Fecha de actualización:** 2026-05-13  
**Estado:** ACTIVO

---

## 1. Objetivo

Trabajar con IA sin repetir arquitectura completa, pero sin perder precisión técnica ni trazabilidad documental.

---

## 2. Regla principal

No reexplicar todo si no cambió, pero sí declarar siempre:
- fase actual
- task activa
- objetivo puntual
- ambiente
- base de datos
- módulo
- archivos a tocar
- archivos prohibidos
- evidencia
- salida esperada

---

## 3. Jerarquía de contexto

| Nivel | Contenido | Cuándo se envía |
|---|---|---|
| 1 | Arquitectura estable | Solo si cambió |
| 2 | Checkpoint operativo | En cada sesión |
| 3 | Caso puntual | Cuando aplica |
| 4 | Feedback estructurado | Después de cada iteración |

---

## 4. Cápsula mínima recomendada

```md
## SESIÓN MADENAT

### Contexto activo
- Fase:
- Task:
- Objetivo:
- Prioridad:

### Ambiente
- Odoo:
- Base de datos:
- Rama / commit:
- Contenedores:
- Módulo:

### Alcance
- Tocar:
- No tocar:

### Evidencia
- Caso:
- Hallazgo actual:
- Riesgo actual:

### Tipo de ayuda
- analizar / proponer / actualizar / paso a paso / consolidar

### Salida esperada
- explicación
- diff
- archivos completos
- checklist
- próximos pasos
```

---

## 5. Regla de actualización por archivo

| Si cambia esto | Archivos a actualizar |
|---|---|
| Foco actual | continuidad + backlog |
| Regla técnica | arquitectura + decision log |
| Flujo operativo | flujo packing + continuidad |
| Cálculo o naming de campos | arquitectura + tests + decision log + continuidad |
| Se cierra una task | backlog + continuidad |
| Riesgo nuevo | continuidad + backlog |
| Forma de colaborar con IA | este archivo |

---

## 6. Regla especial para bugs de naming

Si el bug involucra diferencias entre:
- nombre Python,
- nombre XML,
- nombre en tests,
- nombre documentado,

entonces no basta con arreglar código.  
También hay que actualizar:
- `00_ARQUITECTURA.md`
- `02_CONTINUIDAD.md`
- `03_TESTS.md`
- `04_DECISION_LOG.md`
- `05_BACKLOG.md`

---

## 7. Modos de salida válidos

- explicación primero
- diff y luego archivos
- archivos completos listos para pegar
- paso a paso
- consolidación documental completa

---

## 8. Criterio de éxito

Una sesión se considera bien ejecutada cuando:
- el foco queda claro rápido,
- los cambios aterrizan en los archivos correctos,
- el estado del proyecto queda consistente,
- y el siguiente punto de retoma es explícito.
