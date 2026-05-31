# Estado del Módulo — MADENAT Lumber Core

**Fecha:** 2026-05-13  
**Estado global:** AMARILLO / BLOQUEADO PARCIALMENTE  
**Razón:** El módulo conserva una inconsistencia crítica en `@depends` del feature de largo con unidad.

---

## 1. Qué está estable
- arquitectura modular parcial
- gates documentados
- base T01–T14 consolidada
- parser y service desacoplados
- política de Gate 3 como write único

---

## 2. Qué está bloqueando
- `ValueError` por dependencia a `lengthinputraw`
- inconsistencia entre vista/documentación/código
- instalación no limpia del módulo

---

## 3. Qué no debe asumirse
No debe asumirse que el feature de largo/unidades está cerrado solo porque:
- existen campos documentados,
- existe vista,
- o existe intención de tests.

Mientras el módulo no instale limpio, el feature sigue abierto.

---

## 4. Siguiente acción correcta
Corregir naming y depends del compute de largo, reinstalar el módulo y ejecutar T29–T32.

---

## 5. Prioridad posterior
Retomar Fase 6 financiera únicamente después de estabilizar la base.
