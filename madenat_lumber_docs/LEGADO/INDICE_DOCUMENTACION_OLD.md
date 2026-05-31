# 🗺️ WIKI — Índice Maestro MADENAT

**Estado:** ACTIVO
**Última actualización:** 2026-05-28
**Propósito:** Mapa de navegación del ecosistema documental.

---

## Principio rector

Esta carpeta mantiene una sola fuente de verdad por tema.
Los documentos activos viven en la raíz del repositorio documental.
Todo material histórico, auditorías antiguas, snapshots, versiones externas o documentos reemplazados debe permanecer en `LEGADO/` o `LEGADO_EXTERNOS/` y no debe usarse como fuente principal de trabajo. [file:13][file:31]

---

## Regla de oro en ingeniería

1. Investigar primero.
2. Mapear dependencias.
3. Entender el problema real, no solo el síntoma.
4. Aplicar la solución mínima correcta.
5. Validar impacto.
6. Documentar cambios.
7. Deploy con confianza.

---

### 1. Núcleo Canónico (Verdad Técnica)
- 00_ARQUITECTURA.md: Modelos, Gates y Naming.
- 02_CONTINUIDAD.md: Estado actual y retoma.
- 03_TESTS.md: Matriz de validación.
- 04_DECISIONLOG.md: Reglas inamovibles.
- 05_BACKLOG.md: Tareas pendientes.

### 2. Soporte y Sesiones
- CAPSULA_CONTEXTO.md: Contexto para IA.
- CHECKLIST.md: Guía de sesión.

### `GUIA_PRODUCCION_FINAL.md`
Guía oficial para despliegue, validación operativa y salida controlada a producción.

### `HOJA_RUTA_EJECUTIVA.md`
Vista ejecutiva del avance, hitos y foco actual del proyecto.

### `QUICK_START.md`
Ruta corta de onboarding para retomar rápido el proyecto.

---

## Estructura de lectura recomendada

### Para retomar desarrollo técnico
1. `INDICE_DOCUMENTACION.md`
2. `02_CONTINUIDAD.md`
3. `05_BACKLOG.md`
4. `03_TESTS.md`
5. `00_ARQUITECTURA.md`
Esta secuencia sigue la lógica actual de continuidad viva, backlog priorizado y validación antes de tocar arquitectura en detalle. [file:5][file:7]

### Para validar antes de deploy
1. `GUIA_PRODUCCION_FINAL.md`
2. `06_CHECKLIST.md`
3. `03_TESTS.md`
4. `04_DECISION_LOG.md`
Esta ruta refleja el flujo operativo vigente de validación, criterios de avance y revisión de reglas técnicas activas. [file:7][file:4]

### Para entender contexto general
1. `QUICK_START.md`
2. `HOJA_RUTA_EJECUTIVA.md`
3. `00_ARQUITECTURA.md`
4. `01_FLUJO_PACKING.md`

### Para analizar una contradicción documental
1. Documento canónico del tema.
2. `04_DECISION_LOG.md`
3. `02_CONTINUIDAD.md`
4. Material histórico solo como evidencia contextual. [file:4][file:5]

---

## Política de edición

- No crear documentos nuevos si el tema ya tiene documento canónico asignado. [file:4]
- Actualizar primero el documento dueño del tema.
- Si una decisión cambia arquitectura, continuidad, backlog, validación o criterio operativo, sincronizar los documentos afectados el mismo día. [file:4][file:5][file:7]
- No editar archivos bajo `LEGADO/` salvo necesidad explícita de auditoría histórica. [file:13][file:31]
- No usar documentos en `LEGADO_EXTERNOS/` como fuente vigente. [file:13]
- Si aparece información duplicada, consolidar en el canónico y mover el excedente a legado. [file:4]
- Si un cambio afecta estado real del proyecto, `02_CONTINUIDAD.md` debe actualizarse antes del siguiente checkpoint. [file:5]
- Si un cambio modifica una regla técnica o criterio estructural, `04_DECISION_LOG.md` debe actualizarse el mismo día. [file:4]
- Si un cambio altera validación o criterio de cierre, actualizar `03_TESTS.md` y/o `06_CHECKLIST.md` según corresponda. [file:7]

---

## Material histórico y no canónico

### `LEGADO/`
Contiene documentación histórica, auditorías antiguas, snapshots, inventarios y materiales descontinuados.
Sirve como evidencia o referencia contextual, no como guía principal de trabajo. [file:31]

### `LEGADO_EXTERNOS/`
Contiene variantes, borradores o versiones externas que no forman parte del flujo documental oficial. [file:13]

### `backups/`
Contiene respaldos comprimidos previos a limpiezas, consolidaciones o refactorizaciones documentales. [file:31]

---

## Criterio de verdad

Ante contradicción entre documentos:

1. Manda el documento canónico del tema.
2. Luego manda `04_DECISION_LOG.md` como registro formal de decisión.
3. Luego manda `02_CONTINUIDAD.md` como estado operativo vigente.
4. Los documentos históricos solo sirven como evidencia o referencia contextual. [file:4][file:5]

---

## Mantenimiento obligatorio

Cada cambio importante debe dejar trazabilidad mínima en:

- `02_CONTINUIDAD.md`, si afecta continuidad, estado actual, riesgos, punto de retoma o prioridades. [file:5]
- `04_DECISION_LOG.md`, si cambia una decisión relevante de arquitectura, naming, cálculo, gates o criterio técnico. [file:4]
- `05_BACKLOG.md`, si crea, cierra o re-prioriza trabajo.
- `03_TESTS.md`, si cambia validación, cobertura o casos esperados.
- `06_CHECKLIST.md`, si cambia el criterio operativo de inicio, cierre, validación o deploy. [file:7]

---

## Regla de cierre documental

No se considera cerrado un cambio técnico mientras ocurra alguna de estas condiciones:

- el código cambió y la documentación canónica no refleja el nuevo estado;
- existe discrepancia entre naming en código, vistas, tests y documentación;
- el backlog no refleja la prioridad real;
- la continuidad no deja un punto de retoma claro;
- el criterio operativo de validación quedó desalineado. [file:4][file:5][file:7]

---

## Nota de transición

Las referencias históricas a `MADENAT_ECOSYSTEM_MASTER.md`, `DOCUMENTO_UNICO_REFERENCIA.md`, `ROADMAP.md`, `RESUMEN_AUDITORIA_Y_DOCUMENTACION.md`, `MANIFEST_ENTREGA.md`, así como documentos más antiguos (`ESTADO_MODULO.md`, `GUIA_CONTINUIDAD_TECNICA.md`, etc.), han sido trasladadas a `LEGADO/` y deben considerarse absorbidas, archivadas o relegadas a material histórico.
La navegación oficial actual parte desde este índice y continúa EXCLUSIVAMENTE sobre los documentos canónicos activos definidos arriba. [file:13][file:31]