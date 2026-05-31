# 04 — Decision Log

**Módulo:** MADENAT Lumber Core
**Versión documental:** 6.2.0
**Última actualización:** 2026-05-23
**Estado:** Canonical / activo

---

## Propósito

Registrar las decisiones técnicas que gobiernan arquitectura, flujo funcional, trazabilidad, validación y continuidad.
Este archivo no contiene tareas pendientes ni evidencia de ejecución; solo decisiones que pasan a ser regla del sistema o de la documentación.

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
Se prohíben fallbacks silenciosos para tipo de cambio.

### AD-06 — Protocolo de colaboración con IA
La continuidad se apoya en cápsulas breves y actualización dirigida de archivos canónicos.

---

## 2026-05-03 — Modularización y estabilidad

### AD-07 — Desacoplamiento parcial del monolito
Se extrae parser, workflow, servicio y helpers, pero se acepta temporalmente que `lumber_reception.py` siga concentrando clases principales.

### AD-08 — Lógica compartida en mixins/helpers
Se consolida reutilización de cálculos y utilidades para evitar reglas divergentes.

### AD-09 — Base T01–T14 como núcleo estable
La suite T01–T14 se adopta como el corazón funcional validado del proyecto.

### AD-10 — Fase 6 financiera como siguiente frente mayor
Una vez estabilizada la base operativa, el siguiente frente mayor es `lumber.billing.consolidation.line`.

---

## Compatibilidad Odoo 18

### AD-11 — Uso de `<list>`
En Odoo 18 las vistas de lista deben declararse con `<list>`.

---

## 2026-05-13 — Largo con unidad de ingreso

### AD-12 — `length` en metros como fuente de verdad
`length` se define formalmente como el valor interno canónico para cálculos.

### AD-13 — lengthinputraw como preservación de entrada humana
Se agrega el identificador canónico para el valor crudo de ingreso.

### AD-14 — lengthuom desacoplado del perfil de ingesta
La unidad de largo no debe confundirse con el perfil de cálculo; son conceptos distintos.

### AD-15 — Los cálculos deben leer valor normalizado
Todos los computes volumétricos deben basarse en `length` ya convertido a metros.

### AD-16 — Estabilidad nominal de campos
Toda referencia a la entrada de largo debe utilizar exactamente lengthinputraw para asegurar la estabilidad del registry.

### AD-17 — La incoherencia de naming es bug crítico
Toda discrepancia entre:
- nombre de campo,
- nombre usado en vista,
- nombre usado en `@depends`,
- nombre usado en tests,

se considera bug de primer nivel porque rompe instalación o produce cómputos erróneos.

---

## 2026-05-23 — Gobernanza documental y cierre técnico

### AD-18 — Separación estricta por tipo de documento
Cada documento canónico debe tener una responsabilidad única:
- `02_CONTINUIDAD.md` = estado vivo y punto de retoma.
- `03_TESTS.md` = evidencia y criterios de validación.
- `04_DECISION_LOG.md` = reglas y decisiones permanentes.
- `05_BACKLOG.md` = trabajo pendiente y prioridades activas.
- `06_CHECKLIST.md` = operación de sesión y cierre.

### AD-19 — El backlog no debe mezclar reglas ni evidencia
Si un contenido ya es regla permanente, debe pasar a decision log.
Si ya es estado confirmado, debe pasar a continuidad.
Si ya tiene evidencia, debe vivir en tests.

### AD-20 — La continuidad debe reflejar estado real, no teoría
`02_CONTINUIDAD.md` se define como checkpoint técnico operativo.
Debe permitir retomar trabajo sin reabrir análisis histórico innecesario.

### AD-21 — Las pruebas no se cierran por percepción
Un caso de prueba solo puede cerrarse si existe esperado explícito, resultado real, evidencia y actualización documental coherente.

### AD-22 — La validación de largo/unidades sigue abierta hasta evidencia formal
Aunque el error de `Wrong @depends` fue resuelto, el frente de largo/unidades no se considera cerrado hasta ejecutar y documentar T29, T30, T31 y T32.

### AD-23 — Fase 6 requiere cierre funcional completo
La implementación técnica de `shipment -> consolidation` no basta por sí sola.
La fase solo puede considerarse cerrada con validación UI, confirmación de creación real de registros y trazabilidad documental completa.

### AD-24 — Solución mínima antes que refactor amplio
Ante incidencias activas, primero se investiga, se mapean dependencias y se aplica la corrección mínima segura antes de abrir refactors mayores.

### AD-25 — La documentación se actualiza antes del cierre de sesión
Si cambia naming, cálculo, gates, flujo financiero o criterio de validación, la sesión no se considera cerrada hasta dejar actualizados continuidad, backlog, decision log y tests cuando corresponda.

### AD-26 — Higiene del Repositorio
**Decisión:** Se prohíbe la permanencia de carpetas `.backup` o archivos `.bak` dentro de los módulos de Odoo.
**Motivo:** Evitar colisiones de carga de vistas y mantener la limpieza del empaquetado del módulo.
**Impacto:** Los backups deben residir exclusivamente en `LEGADO/` dentro del repositorio documental.

---

## Riesgos registrados

| ID | Riesgo | Mitigación |
|---|---|---|
| R-01 | Integración financiera incompleta | cerrar Fase 6 con validación funcional y documental |
| R-02 | Warnings XML | limpieza progresiva |
| R-03 | Tolerancias matemáticas no formalizadas | parametrización futura |
| R-04 | Monolito parcial | refactor posterior |
| R-05 | Incoherencia de naming | resuelto el 23-mayo-2026 (lengthinputraw) |

---

## Prioridad actual

### Prioridad 0
Mantener consistencia del feature de largo/unidades hasta cerrar T29–T32.

### Prioridad 1
Revalidar y documentar formalmente T29–T32.

### Prioridad 2
Cerrar validación funcional de Fase 6 financiera.

### Prioridad 3
Reducir documentación satélite y fortalecer solo el núcleo canónico.

---

## Regla de mantenimiento

Toda decisión que cambie:
- naming de campos,
- política de cálculo,
- gates,
- flujo financiero,
- o arquitectura documental,

debe reflejarse aquí el mismo día.

## 2026-05-23 - Reglas de Calidad y Escalabilidad

### DEC-2026-05-23-PERF-01
**Decisión:** el endurecimiento de calidad técnica y la optimización de performance para altos volúmenes de datos pasan a ser un requisito de diseño permanente (regla arquitectónica), no un ítem aislado del backlog.
**Impacto:** cualquier desarrollo futuro (como la integración contable) debe diseñarse considerando volúmenes de producción masivos.

---

## 2026-05-23 - Consolidación documental y limpieza de ruido histórico

### DEC-2026-05-23-DOC-01
**Decisión:** consolidar la documentación activa en un núcleo canónico único por tema y mover inventarios, auditorías históricas, snapshots, dashboards auxiliares y variantes externas a `LEGADO/` o `LEGADO_EXTERNOS/`.

**Motivo:** existía ruido documental, duplicidad de contexto y referencias obsoletas que dificultaban la continuidad técnica y elevaban el riesgo de retomar trabajo desde una fuente incorrecta.

**Impacto:**
- Se fortalece `INDICE_DOCUMENTACION.md` como mapa maestro.
- Se reduce ambigüedad sobre qué documento editar.
- Se separa explícitamente documentación vigente de material histórico.
- Se mejora onboarding, continuidad y gobernanza documental.

**Regla operativa derivada:** no crear documentos paralelos para temas ya cubiertos por un archivo canónico; actualizar el documento dueño del tema y registrar la decisión si el cambio afecta arquitectura, operación o proceso documental.