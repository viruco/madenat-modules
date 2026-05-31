# MADENAT — Protocolo de Trabajo con IA

**Versión:** 4.1.0  
**Fecha:** 2026-05-03  
**Estado:** ACTIVO ✅

---

## 1. Objetivo

Este protocolo existe para trabajar con la IA sin volver a explicar arquitectura, backlog, restricciones, versiones, base de datos o contexto del proyecto en cada sesión.

La idea central es simple:
- la arquitectura se explica una vez,
- el estado vivo se resume en una cápsula breve,
- los cambios se pasan como delta,
- y la retroalimentación se convierte en actualizaciones concretas de archivos.

---

## 2. Regla principal

No volver a contar toda la historia del proyecto si no cambió.

### Sí se debe enviar al iniciar una sesión
- Fase actual.
- Task activa.
- Objetivo puntual.
- Ambiente.
- Base de datos.
- Rama o commit.
- Módulo.
- Archivos a tocar.
- Archivos prohibidos.
- Evidencia o caso base.
- Salida esperada.

### No hace falta repetir si no cambió
- Arquitectura congelada.
- Regla de Gates.
- Triple capa.
- Política de tipo de cambio.
- Regla GPS vs interiores.
- Backlog histórico ya documentado.

---

## 3. Jerarquía de contexto

| Nivel | Contenido | Cuándo se envía |
| ----- | --------- | --------------- |
| Nivel 1 | Arquitectura estable | Solo si cambió |
| Nivel 2 | Checkpoint operativo | Al iniciar cada sesión |
| Nivel 3 | Caso o bug puntual | Cuando trabajamos algo específico |
| Nivel 4 | Feedback de iteración | Después de cada propuesta |

Traducción práctica:
- Nivel 1 vive en los documentos.
- Nivel 2 se manda siempre.
- Nivel 3 se manda cuando aplica.
- Nivel 4 aparece al revisar la respuesta.

---

## 4. Cápsula de contexto

Este es el bloque mínimo que debes enviar al comenzar una sesión:

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
- Módulo(s):

### Alcance
- Tocar:
- No tocar:

### Caso / evidencia
- Guía / OC / archivo / bug:
- Hallazgo actual:
- Riesgo actual:

### Tipo de ayuda
- Analizar / proponer / actualizar / trabajar paso a paso / consolidar / migrar

### Salida esperada
- explicación
- diff
- archivos completos
- checklist
- pasos siguientes
```

---

## 5. Variables mínimas

Si quieres que yo trabaje contigo sin reexplicar todo, estas son las variables mínimas:

| Variable | Ejemplo | Para qué sirve |
| -------- | ------- | -------------- |
| Proyecto | MADENAT | Confirma contexto general |
| Versión Odoo | 18 CE | Evita respuestas de otra versión |
| Base de datos | `madenat_test` | Aterriza comandos y validaciones |
| Rama / commit | `feature/packing-flow` | Saber si hablamos de línea viva o migración |
| Módulo activo | `madenat_lumber_core` | Foco técnico |
| Fase | Fase 3 | Priorización |
| Task | Task 3.2 | Define alcance exacto |
| Caso base | Guía 40597 | Evidencia mínima |
| Ambiente | Docker local / staging / producción | Nivel de riesgo |
| Restricción | no tocar arquitectura / no tocar menús | Delimita acción |

---

## 6. Formatos de trabajo

### Modo análisis

```md
## SESIÓN MADENAT
- Fase: Fase 3 — Flujo Packing
- Task: Task 3.2 — Conciliación matemática
- Objetivo: entender por qué no cuadra MBF
- Odoo: 18 CE
- BD: madenat_test
- Rama: feature/packing
- Tocar: análisis solamente
- No tocar: archivos aún
- Caso: Guía 40597
- Salida esperada: diagnóstico + plan
```

### Modo actualización directa

```md
## SESIÓN MADENAT
- Fase: Fase 3
- Task: Task 3.3
- Objetivo: cerrar riesgo package_no → lot_name
- Odoo: 18 CE
- BD: madenat_test
- Rama: bugfix/lot-name
- Tocar: flujo packing, tests, backlog
- No tocar: arquitectura
- Salida esperada: archivos completos actualizados
```

### Modo guiado paso a paso

```md
## SESIÓN MADENAT
- Modo: paso a paso
- Regla: no avances al siguiente punto sin mi confirmación
- Objetivo: revisar primero el alcance, luego continuidad, luego tests
```

### Modo migración

```md
## SESIÓN MADENAT
- Tema: migración
- Desde: Odoo 18 CE / BD actual
- Hacia: nueva rama o nueva BD
- Riesgo principal: compatibilidad de vistas / datos / modelo
- Salida esperada: plan de migración, riesgos, orden de trabajo
```

---

## 7. Feedback loop

La retroalimentación ideal no debe ser solo “falta algo”. Debe decir:
- qué está bien,
- qué está mal,
- qué falta,
- qué quieres que cambie,
- y qué salida esperas ahora.

```md
## FEEDBACK MADENAT

### Qué está bien
-

### Qué está mal o incompleto
-

### Qué quiero cambiar
-

### Nivel de cambio
- ajuste menor / cambio estructural / reemplazo completo

### Salida esperada
- explicación
- archivos completos
- solo diff
- checklist
```

---

## 8. Regla de actualización por archivo

| Si cambia esto | Archivos a actualizar |
| -------------- | --------------------- |
| Cambia el foco actual | continuidad + backlog |
| Cambia una regla técnica | arquitectura + decision log |
| Cambia el flujo operativo | flujo packing + continuidad |
| Cambia un cálculo | arquitectura + tests + decision log |
| Se cierra una task | backlog + continuidad |
| Se detecta un riesgo nuevo | continuidad + backlog |
| Se valida un caso real | tests |
| Cambia la forma de colaboración con IA | trabajo con IA + continuidad si afecta proceso |

---

## 9. Variables vigentes

Usa este formato breve cuando solo quieras que yo esté enterado del estado actual:

```md
### Variables vigentes
- Odoo: 18 CE
- DB: madenat_test
- App container: odoo18_app
- DB container: odoo18_db
- Módulo principal: madenat_lumber_core
- Rama: feature/packing-flow
- Caso base: 40597 / MC2603-306
- Restricción: no tocar arquitectura congelada
```

---

## 10. Cambio de contexto

### Si cambia solo la base de datos
```md
Cambio de contexto:
- Antes: DB `madenat_test`
- Ahora: DB `madenat_uat`
- Motivo: validación funcional con data más real
- Mantener igual: Odoo 18 CE y rama actual
```

### Si cambia la versión o hay migración
```md
Cambio de contexto:
- Desde: Odoo 18 CE
- Hacia: rama de migración o ajuste mayor
- Riesgo: vistas, modelos, campos y manifest
- Quiero: plan de migración antes de tocar archivos
```

---

## 11. Cómo no reexplicar la arquitectura

### Si la arquitectura no cambió
```md
Arquitectura: sin cambios, sigue vigente la congelada.
```

### Si el backlog no cambió
```md
Backlog: sin cambios, seguimos en Task X.
```

### Si solo cambió el bug o el foco
```md
Nuevo hallazgo: el MBF no cuadra con f5085 en líneas Blanks.
Objetivo de hoy: revisar cálculo y dejar tests.
```

---

## 12. Cómo pedirme la salida

Puedes pedirme la salida en cualquiera de estos formatos:
- “Explícame primero y no actualices archivos”.
- “Dame diff y luego archivos finales”.
- “Entrégame archivos completos listos para pegar”.
- “Trabajemos paso a paso”.
- “Consolida y resuelve contradicciones”.

---

## 13. Protocolo ideal de una sesión

### Paso 1
Tú me envías cápsula de contexto.

### Paso 2
Yo te respondo qué entendí, qué toca, qué no toca y el plan corto.

### Paso 3
Tú corriges prioridad si hace falta.

### Paso 4
Yo actualizo o analizo según el modo pedido.

### Paso 5
Tú das feedback estructurado.

### Paso 6
Yo cierro la iteración dejando:
- qué quedó,
- qué cambió,
- qué sigue,
- y desde dónde retomar.

---

## 14. Criterio de éxito

Una sesión está bien llevada cuando:
- no tuviste que repetir toda la arquitectura,
- el foco quedó claro en menos de un minuto,
- el cambio aterrizó en los archivos correctos,
- la retroalimentación se tradujo en acciones,
- y el siguiente checkpoint quedó explícito.