# PLAN DE VENTANA OPERATIVA — Fase E (eliminación desde la UI)

> La eliminación de la Fase E la ejecuta **una persona desde el navegador**. Por eso **no**
> se detiene `odoo18_app` (a diferencia de las Fases B/C, que usaron procesos one-shot).

## Principio

La ventana controlada aquí es **operativa**, no de proceso:
- **Un solo operador** en la sesión de Odoo (el que verifica/autoriza).
- **Sin otras sesiones** ejecutando operaciones sobre Intake/Guías durante el clic.
- **Sin procesos batch/importaciones** en marcha.
- La sesión de navegador **permanece disponible** (el servicio sigue Up).

## Preparación (antes del clic)

1. Confirmar `odoo18_app` **Up** (HTTP `/web/login` = 200) y `odoo18_db` healthy.
2. Confirmar que **no hay otras sesiones** activas relevantes (usuarios en Intake) y que no
   hay importaciones/lotes en curso.
3. Confirmar el respaldo protegido utilizable (`backups/FASE_B_20261007_153214/`).
4. Abrir el asistente de la guía **15183 / 33152** y **re-verificar en vivo**:
   - `Estado = Cancelado`.
   - `N° de bloqueadores = 0`; sin alert rojo de precondiciones.
   - Nota de atribución presente; `EMB-00227` **no** listado como bloqueador.
   *(Los campos del asistente se recalculan en vivo al abrirlo, por lo que esta re-verificación
   es la comprobación final antes de escribir.)*

## Ejecución

5. Seleccionar **A. Eliminar definitivamente**, escribir el **Motivo aprobado** y marcar el
   check de confirmación.
6. Pulsar **Ejecutar** (una sola vez). El asistente **revalida** las dependencias y toma su
   candado (`pg_advisory_xact_lock`) antes del `unlink()`.

## Verificación inmediata

7. Observar la notificación y el retorno a la Consola (la guía desaparece).
8. Revisar `docker logs --since <hora> odoo18_app` → sin errores atribuibles.
9. Confirmar: guía 33152 ya no existe; recepción 1369 y cadena 436→7813→7814 intactas.

## Contingencia

- Si la acción **falla**: **no** forzar, **no** borrar por SQL, **no** repetir sin investigar.
  Detener e informar (modelo/ID/relación/causa del bloqueo).
- Recuperación (si se requiriera): **restaurar dump + filestore** (no es `git apply -R`).

## Límite declarado (concurrencia general)

El candado `pg_advisory_xact_lock` **solo** serializa eliminaciones Modo A de la **misma**
guía; los **creadores de dependencias no lo toman**. Existe una **ventana residual** entre
la revalidación y el `unlink()`. La ventana operativa (un solo operador, sin otros
escritores) **reduce** el riesgo de este caso, pero **no** resuelve la concurrencia general
del producto.

---

## Nota sobre el mensaje recibido

El punto **4** del mensaje ("…Preparar la ventana operativa: definir cómo mantener disponible
el navegador para ejec[utar]…") quedó **truncado**. Este plan responde a ese objetivo. Si
había indicaciones adicionales (p. ej. horario de la ventana, operador designado, o
restricciones de red/UI), indícalo y lo incorporo antes de la Fase E.
