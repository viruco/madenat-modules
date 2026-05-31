### 📑 04 — DECISION LOG (REGISTRO DE DECISIONES TÉCNICAS)

**Módulo:** MADENAT Lumber Core  
**Versión de Documento:** 5.0.1  
**Última Actualización:** 2026-05-03  
**Estado:** Canonical / Post-Refactor Modular / Ready for Fase 6

---

## Propósito

Este documento registra las decisiones técnicas que gobiernan la arquitectura, el flujo funcional y la continuidad del proyecto MADENAT Lumber Core. Su objetivo es mantener una fuente de verdad única, auditable y consistente con el estado real del módulo.

---

## 2026-04-08 — Cimentación del proyecto

### [AD-01] Base documental canónica única
- **Decisión:** Se define una base documental única para evitar checkpoints narrativos incompatibles.
- **Motivo:** Existían versiones parciales del estado del proyecto con distintos focos y niveles de avance.
- **Impacto:** Arquitectura, Flujo, Backlog y Tests viven en archivos independientes pero sincronizados. Se elimina la dispersión de información.

### [AD-02] Foco en flujo integral y pruebas matemáticas
- **Decisión:** El foco del proyecto se orienta al flujo integral del packing y a la validación matemática y funcional.
- **Motivo:** Una vez estables los gates, la prioridad es garantizar que volumen físico, compra y embarque coincidan con la trazabilidad del lote.
- **Impacto:** Priorización de tareas de conciliación matemática: `vol_physical_m3`, `vol_purchase_m3`, `vol_mbf`.

### [AD-03] Regla de menús (GPS vs interiores)
- **Decisión:** Los menús nacen en el árbol principal de MADENAT y las vistas solo describen interiores.
- **Motivo:** Evitar menús huérfanos o desplazados entre módulos al instalar o desinstalar.
- **Impacto:** `lumber_core_menu.xml` actúa como punto de navegación principal. Los archivos `*_views.xml` solo contienen la interfaz.

### [AD-04] Gate 3 como único write real de inventario
- **Decisión:** Gate 3 es el único punto autorizado para crear registros de stock real en Odoo.
- **Motivo:** Blindaje funcional y auditoría. Se evita la creación de registros parciales o fantasma durante validaciones previas.
- **Impacto:** Gates 0, 1 y 2 no generan efectos secundarios en `stock.move` o `stock.lot`.

### [AD-05] Política financiera de cambio explícito
- **Decisión:** Se prohíbe cualquier fallback silencioso de tipo de cambio en recepciones.
- **Motivo:** Evitar contaminación financiera y cierres de mes con datos no confiables.
- **Impacto:** Si falta el dato financiero, el sistema debe bloquear el flujo y exigir ingreso explícito.

### [AD-06] Protocolo de colaboración con IA
- **Decisión:** La colaboración con IA se estandariza mediante una cápsula de contexto breve y feedback accionable.
- **Motivo:** Evitar reexplicar arquitectura, restricciones y alcance en cada sesión.
- **Impacto:** Uso de cápsulas que incluyan fase, task, archivos prohibidos y salida esperada.

---

## 2026-05-03 — Escalabilidad y refactor modular

### [AD-07] Desacoplamiento del monolito
- **Decisión:** Extraer lógica de `lumber_reception.py` hacia servicios especializados.
- **Motivo:** El archivo original era inmanejable y bloqueaba la implementación de la Fase 6.
- **Impacto:** Código modular, con responsabilidades únicas y mejor testabilidad.

### [AD-08] Adopción de mixins para reglas compartidas
- **Decisión:** Centralizar cálculos matemáticos y validaciones en `mixin_lumber_utils.py`.
- **Motivo:** Reutilización de lógica para futuros módulos de guías de proceso, despacho y costeo.
- **Impacto:** Se unifica el estándar matemático para los módulos MADENAT.

### [AD-09] Cobertura de tests core 14/14
- **Decisión:** Se implementa y valida la suite completa de 14 casos de prueba core.
- **Motivo:** Asegurar que el refactor no introdujo regresiones en trazabilidad y persistencia.
- **Impacto:** Estado **PRODUCTION READY** alcanzado.

### [AD-10] Inicio de Fase 6: integración financiera
- **Decisión:** El foco inmediato se desplaza a la creación del modelo `lumber.billing.consolidation.line`.
- **Motivo:** El motor de inventario está estable; la brecha operativa actual es el costeo real y la vinculación con facturas de proveedor.
- **Impacto:** La Fase 6 pasa a ser prioridad técnica inmediata.

---

## Compatibilidad Odoo 18

### [AD-11] Uso de `<list>` en lugar de `<tree>`
- **Decisión:** En Odoo 18, las vistas tipo lista deben declararse con `<list>`.
- **Motivo:** Odoo 18 introdujo la sustitución de `tree` por `list`, y el upgrade code pudo generar transformaciones defectuosas si no se corrige el XML.
- **Impacto:** Las vistas listas deben quedar validadas con atributos dentro del tag `<list>` y no fuera de él.

---

## Riesgos registrados

| ID | Riesgo | Mitigación |
| :--- | :--- | :--- |
| **R-01** | Inconsistencia de facturación | Implementación mandatoria de `lumber.billing.consolidation.line` en Fase 6. |
| **R-02** | Warnings visuales en XML | Limpieza de iconos FA y revisión de vistas en Odoo 18. |
| **R-03** | Tolerancias matemáticas | Parametrización de umbrales de Gate 2 por tipo de producto. |
| **R-04** | Migración de vistas `tree` a `list` | Validación manual del XML tras upgrade y revisión de atributos dentro del tag correcto. |

---

## Prioridad actual

### Fase 6 — Integración financiera
El siguiente paso es crear `lumber.billing.consolidation.line` como modelo de consolidación para costeo, facturación y trazabilidad financiera.

---

**Registro de decisiones técnicas auditado por el equipo de ingeniería de MADENAT.**