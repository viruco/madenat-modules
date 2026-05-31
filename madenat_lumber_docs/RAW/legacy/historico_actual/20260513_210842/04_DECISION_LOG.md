# 04 — Decision Log

**Módulo:** MADENAT Lumber Core  
**Versión documental:** 6.0.0  
**Última actualización:** 2026-05-13  
**Estado:** Canonical / activo

---

## Propósito

Registrar las decisiones técnicas que gobiernan arquitectura, flujo funcional, trazabilidad y continuidad.

---

## 2026-04-08 — Cimentación

### AD-01 — Base documental canónica única
Se define una base documental central para evitar versiones parciales incompatibles.

### AD-02 — Foco en flujo integral y matemática reproducible
La validación del módulo se centra en que documento, staging, exportación y stock puedan reconciliarse matemáticamente.

### AD-03 — Regla de menús
Los menús viven en árbol principal; las vistas describen interiores.

### AD-04 — Gate 3 como único write real
Gate 3 es el único punto autorizado para escribir inventario real.

### AD-05 — Tipo de cambio explícito
Se prohíben fallbacks silenciosos para TC.

### AD-06 — Protocolo de colaboración con IA
La continuidad se apoya en cápsulas breves y actualización dirigida de archivos.

---

## 2026-05-03 — Modularización y estabilidad

### AD-07 — Desacoplamiento parcial del monolito
Se extrae parser, workflow, servicio y helpers, pero se acepta temporalmente que `lumber_reception.py` siga concentrando clases principales.

### AD-08 — Lógica compartida en mixins/helpers
Se consolida reutilización de cálculos y utilidades para evitar reglas divergentes.

### AD-09 — Base T01–T14 como núcleo estable
Se toma la suite T01–T14 como el corazón funcional validado del proyecto.

### AD-10 — Fase 6 financiera como siguiente frente mayor
Una vez estabilizada la base, el siguiente frente es `lumber.billing.consolidation.line`.

---

## Compatibilidad Odoo 18

### AD-11 — Uso de `<list>`
En Odoo 18 las vistas de lista deben declararse con `<list>`.

---

## 2026-05-13 — Largo con unidad de ingreso

### AD-12 — `length` en metros como fuente de verdad
Se define formalmente que `length` es el valor interno canónico para cálculos.

### AD-13 — `length_input_raw` como preservación de entrada humana
Se agrega el concepto de valor crudo de ingreso para no perder la semántica del operador.

### AD-14 — `length_uom` desacoplado del perfil de ingesta
La unidad de largo no debe confundirse con el perfil de cálculo. Son conceptos distintos.

### AD-15 — Los cálculos deben leer valor normalizado
Todos los computes volumétricos deben basarse en `length` ya convertido.

### AD-16 — No cerrar T29–T32 sin estabilidad de instalación
La mera existencia de vista/documentación no valida el feature. Si el registry falla por `@depends`, el cambio sigue abierto.

### AD-17 — La incoherencia de naming es bug crítico
Toda discrepancia entre:
- nombre de campo,
- nombre usado en vista,
- nombre usado en `@depends`,
- nombre usado en tests,

se considera bug de primer nivel porque rompe instalación o produce cómputos erróneos.

---

## Riesgos registrados

| ID | Riesgo | Mitigación |
|---|---|---|
| R-01 | Integración financiera ausente | abordar Fase 6 después de estabilizar instalación |
| R-02 | Warnings XML | limpieza progresiva |
| R-03 | Tolerancias matemáticas no formalizadas | parametrización futura |
| R-04 | Monolito parcial | refactor posterior |
| R-05 | `lengthinputraw` vs `length_input_raw` | corrección inmediata de código y revalidación |

---

## Prioridad actual

### Prioridad 0
Reparar coherencia del feature de largo/unidades para permitir instalación limpia del módulo.

### Prioridad 1
Revalidar T29–T32 tras reparación.

### Prioridad 2
Retomar Fase 6 financiera.

---

## Regla de mantenimiento

Toda decisión que cambie:
- naming de campos,
- política de cálculo,
- gates,
- o arquitectura,

debe reflejarse aquí el mismo día.
