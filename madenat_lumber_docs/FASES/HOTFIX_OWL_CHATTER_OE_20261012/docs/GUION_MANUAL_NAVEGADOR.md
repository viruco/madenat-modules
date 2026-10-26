# Guion de comprobación MANUAL en navegador — HOTFIX OWL chatter (`<chatter/>`)

**Estado:** **PENDIENTE.** No hay navegador en el entorno; la corrección está implementada y validada por
servidor (arch efectivo + ORM). Una validación XML/ORM **no** demuestra que el cliente Owl evalúe la vista sin
errores. Ejecutar este guion en `http://localhost:8069` (base `madenat_test`).

> **NO** usar `IMP04823` ni `IMP02220` para escribir datos. Trabajar con **un documento de PRUEBA** (borrador).

## Preparación
1. `docker compose up -d` (o confirmar `odoo18_app`/`odoo18_db` arriba). Abrir `localhost:8069`.
2. Menú **Logística / Exportación → Rebaja de etiquetas** (`menu_madenat_sv_assignment`).
3. Abrir una etiqueta SV (Lote Volumen) → botón **«Registrar rebaja»**.
4. Registrar un documento de PRUEBA: seleccionar cantidades y pulsar **«Guardar»** (queda en `draft`).
   Alternativa de solo lectura: abrir un documento existente desde **«Historial de rebajas» /
   «Ver historial completo»**.

## VIEW-01 — El formulario abre sin OwlError
1. Abrir el documento de prueba (draft). Luego repetir con documentos en **pending**, **applied**,
   **cancelled** y **reversed**.
2. Abrir la consola del navegador (`F12` → Console).
3. **Esperado:** el formulario abre; **ningún** `OwlError` / `TypeError … 'includes'` / `urlRelation`.
4. Repetir con `?debug=assets`.

## VIEW-02 — La lista de historial NO ofrece «Agregar una línea»
1. Bajar al **chatter** (parte inferior del documento).
2. Pestaña **«Mensajes»** (`message_ids`) y **«Seguidores»** (`message_follower_ids`).
3. **Esperado:** en **ninguna** de las dos listas aparece **«Agregar una línea»**.

## VIEW-03 — Los datos existentes siguen visibles
1. En el chatter, verificar que se ven los mensajes y seguidores existentes (fecha, autor, asunto, etc.).
2. **Esperado:** contenido presente y navegable; sin columnas vacías forzadas.

## VIEW-04 — No se puede crear/editar/borrar filas del chatter desde el formulario
1. Intentar crear una fila en el chatter.
2. **Esperado:** imposible (no hay «Agregar una línea»); sin errores en consola.

## VIEW-06 — Recorrido de regresión (mismo documento de prueba)
Guardar → Aplicar → Volver → Continuar preparación → Anular → Reabrir (si aplica) → Reversar (si aplica).
**Esperado:** cada acción funciona como antes; **sin** OwlError.

## VIEW-07 — Sin efectos físicos
1. Antes/después: verificar que **no** cambian cantidades en stock, movimientos ni reservas
   (operación **documental**).
2. **Esperado:** sin cambios físicos.

## Capturas/evidencia a adjuntar
- `before`: el formulario mostrando las listas con «Agregar una línea» (antes) — si aún se conserva copia.
- `after`: el mismo formulario con el chatter estándar (Mensajes/Seguidores) y **sin** «Agregar una línea».
- Consola: **sin** `OwlError`.

## Criterio de cierre
El formulario abre y la tabla se muestra sin OwlError; no existe «Agregar una línea» en el chatter; los
registros existentes no se modifican; ninguna operación de negocio cambia de comportamiento.
