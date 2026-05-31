# Hoja de Ruta Ejecutiva — MADENAT Lumber Core

**Estado:** ACTIVO  
**Última actualización:** 2026-05-23  
**Objetivo:** mostrar el foco ejecutivo real del proyecto sin perder alineación con la documentación técnica canónica.

---

## 1. Estado general

El proyecto mantiene una base funcional sólida y una documentación mucho más ordenada que en fases anteriores.  
La suite base T01–T14 se considera el núcleo estable del negocio y la Fase 6 financiera ya no está ausente a nivel estructural, porque existe una acción manual desde shipment para crear consolidación de facturación. [file:5][file:4]

---

## 2. Foco ejecutivo actual

La prioridad ya no es “seguir agregando features” sin control.  
El foco actual es cerrar correctamente el feature de largo con unidad de ingreso, dejar evidencia formal de T29–T32 y validar de punta a punta el flujo manual de consolidación antes de ampliar automatización financiera. [file:5][file:7]

---

## 3. Prioridades por orden

1. Confirmar coherencia total entre documentación, vistas, tests y código para largo/unidades. [file:5][file:4]
2. Ejecutar y registrar T29–T32 con evidencia reproducible. [file:5][file:7]
3. Validar funcionalmente la Fase 6 manual desde shipment en `delivered` hasta consolidación creada. [file:5]
4. Repriorizar backlog financiero sobre una base ya validada. [file:5][file:4]
5. Mantener documentación canónica sincronizada sin volver a fragmentar el estado. [file:13][file:7]

---

## 4. Riesgos activos

| Riesgo | Severidad | Estado |
|---|---|---|
| Constraint `stock_lot_check_cost_positive` [file:5] | Alta [file:5] | Abierto [file:5] |
| Modelo financiero aún incompleto [file:5][file:4] | Alta [file:5] | Abierto [file:5] |
| Warnings XML menores [file:5][file:4] | Media [file:5] | Abierto [file:5] |
| Monolito parcial en `lumber_reception.py` [file:5][file:4] | Media [file:5] | Abierto [file:5] |

---

## 5. Resultado esperado del siguiente ciclo

Al cierre del siguiente ciclo deberían existir cinco resultados visibles:

- módulo actualizando limpio;
- T29–T32 ejecutadas y registradas;
- flujo manual shipment → consolidation validado;
- continuidad y backlog alineados al estado real;
- criterio de deploy basado en evidencia y no en percepción. [file:5][file:7]

---

## 6. Criterio ejecutivo de avance

Se considera que el proyecto avanza de forma sana cuando:

- el módulo instala sin romper registry;
- las pruebas base siguen firmes;
- los escenarios nuevos quedan evidenciados;
- la documentación cuenta la misma historia que el código;
- el siguiente frente se abre solo después de cerrar el actual. [file:7][file:4][file:5]

---

## 7. Próximo frente mayor

Una vez cerrada la validación de largo/unidades y del flujo manual de consolidación, el siguiente frente mayor vuelve a ser la evolución de la Fase 6 financiera con base documental y funcional estable. [file:4][file:5]