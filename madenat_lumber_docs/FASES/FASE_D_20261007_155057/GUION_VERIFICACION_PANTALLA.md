# GUION BREVE — Verificación de pantalla (Fase D)

Objetivo: verificar en el navegador que el asistente **ya no bloquea** la guía y que
**EMB-00227 no cuenta como documento propio**. **No** pulsar "Ejecutar".

- Entorno: `madenat_test` en `odoo18_app` → `http://127.0.0.1:8069` (o `http://odoo18.localhost`).
- Usuario: autorizado con Operaciones/Jefatura (p. ej. **Cristhian Elgueta**).

## Pasos

1. **Iniciar sesión** con el usuario autorizado y abrir **Intake (Ingreso de Madera)**.
2. Localizar la guía **`15183`** y abrirla. Confirmar que el **Estado = Cancelado**
   (badge `cancelled`).
3. Abrir el asistente **"Ciclo de vida de la guía"** (botón desde la Consola).
   Debe mostrarse un asistente **nuevo** con `N° Guía = 15183` y `Estado = Cancelado`.
4. En **"Modo de ciclo de vida"** seleccionar **"A. Eliminar definitivamente"**.
5. Escribir un **"Motivo"** (obligatorio). Dejar el check
   *"Confirmo explícitamente…"* **sin marcar** (no se va a ejecutar).
6. Verificar el bloque **"Diagnóstico de bloqueadores"**:
   - `N° de bloqueadores` = **0**.
   - **No** aparece lista de bloqueadores.
   - **No** aparece el alert rojo *"El modo seleccionado no cumple sus precondiciones."*
7. Verificar la nota **"Atribución documental (no bloqueante)"**:
   - Debe indicar que **1 albarán con número coincidente NO vinculado a la guía
     pertenece a otro documento y no cuenta como dependencia** (espeja el picking
     `EMB-00227`, de la recepción 1369).
   - **EMB-00227 NO debe aparecer** en la lista de bloqueadores como documento propio.
     (La nota muestra el **conteo**, no el nombre del documento ajeno.)
8. **NO pulsar "Ejecutar"** ni "Eliminar". **Capturar la pantalla.**

## Registro de evidencia (rellenar por quien verifica)

| Campo | Valor |
|---|---|
| Quién verificó (nombre/usuario) | _____ |
| Fecha y hora | _____ |
| Base / URL | `madenat_test` / _____ |
| Guía / ID verificada | 15183 / 33152 |
| Estado mostrado | Cancelado |
| N° de bloqueadores mostrado | _____ (esperado: 0) |
| ¿Aparece EMB-00227 como bloqueador? | No (esperado) |
| ¿Nota de atribución presente? | Sí (esperado) |
| Ruta a la captura de pantalla | _____ |
| Resultado | _____ |

> Nota: **no** se declara verificada la UI de navegador hasta recibir esta evidencia
> del usuario. La prueba automatizada previa fue a nivel de framework (`Form`), no de
> navegador real.
