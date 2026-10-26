# CHECKLIST MANUAL EN NAVEGADOR — VIEW-01 y VIEW-04 (para Mauricio)

**FASE 7 · 2026-10-15 · PENDIENTE DE EJECUCIÓN MANUAL.**
Cline **no** puede ejecutarla (no hay navegador en el entorno) y **no** puede declararla cumplida.
Se entrega lista para ejecutar; debe firmarla quien la ejecute.

**Objetivo:** comprobar en cliente (Owl) que los formularios con chatter **abren sin `OwlError`** y que las
listas del chatter **no** ofrecen «Agregar una línea». Cubre los dos frentes del arreglo:
**(A)** las vistas de **Motonave/Viaje** de `madenat_lumber_shipping_core` (commit `a691256`, FASE 5) y
**(B)** el **documento de rebaja** `madenat.sv.imputation` (HOTFIX OWL, expediente
`HOTFIX_OWL_CHATTER_OE_20261012/`).

> ⚠️ **NO** usar `IMP04823` ni `IMP02220` para escribir. Trabajar con un **documento de PRUEBA** en borrador
> (o solo lectura). El objetivo es de renderizado, no de negocio.

---

## Preparación

1. Confirmar servicios arriba (`odoo18_app`, `odoo18_db`) y abrir `http://localhost:8069` (base `madenat_test`).
2. Abrir la consola del navegador: `F12` → **Console** (limpiarla antes de cada paso).
3. Tener a mano la versión de Odoo (`Ajustes → Acerca de`) y el navegador usado.
4. Anotar la hora de inicio.

---

## A. Vistas de `shipping_core` (arreglo del XML heredado)

### A1 — Motonave (`shipping.vessel`)
1. Menú **Logística / Exportación → Motonaves** (buscar `Motonave`).
2. Abrir cualquier motonave existente (o crear una de PRUEBA y **no** guardar cambios de negocio).
3. Bajar al final del formulario.
4. Intentar la acción del encabezado **«Ver Embarques de esta Motonave»** (solo debe **abrir la lista filtrada**;
   **no** reasigna nada).

| # | Verificación | Esperado | Resultado (✔/✘) | Observación |
|---|---|---|---|---|
| A1.1 | El formulario abre | Sin `OwlError` en consola | | |
| A1.2 | Chatter al pie | Pestañas **Mensajes / Seguidores** estándar | | |
| A1.3 | Botón «Ver Embarques de esta Motonave» | Abre lista de Embarques filtrada por la motonave | | |
| A1.4 | Consola | **Sin** `TypeError … 'includes'` / `urlRelation` | | |

### A2 — Viaje (`shipping.voyage`)
1. Menú **Logística / Exportación → Viajes**.
2. Abrir un viaje y bajar al final del formulario.

| # | Verificación | Esperado | Resultado (✔/✘) | Observación |
|---|---|---|---|---|
| A2.1 | El formulario abre | Sin `OwlError` en consola | | |
| A2.2 | Chatter al pie | Pestañas estándar, sin tablas editables | | |

---

## B. Documento de rebaja (`madenat.sv.imputation`) — VIEW-01 y VIEW-04 originales

**Preparación B:** menú **Logística / Exportación → Rebaja de etiquetas**, abrir un SV → **«Registrar rebaja»**,
o abrir un documento del **Historial de rebajas** (solo lectura).

| # | Verificación | Esperado | Resultado (✔/✘) | Observación |
|---|---|---|---|---|
| **VIEW-01** | Abrir el documento de PRUEBA en `draft` (y repetir en `pending`, `applied`, `cancelled`, `reversed`) y con `?debug=assets` | El formulario **abre**; **ningún** `OwlError` / `TypeError … 'includes'` / `urlRelation` en consola | | |
| **VIEW-02** | Bajar al **chatter** → pestañas **Mensajes** y **Seguidores** | En **ninguna** aparece **«Agregar una línea»** | | |
| **VIEW-03** | Revisar mensajes/seguidores existentes | Contenido visible (fecha, autor, asunto); sin columnas vacías forzadas | | |
| **VIEW-04** | Intentar crear/editar/borrar filas del chatter desde el formulario | **Imposible** (no existe «Agregar una línea»); sin errores en consola | | |

---

## Evidencia a adjuntar

- Captura del formulario de **Motonave** y de **Viaje** con el chatter al pie.
- Captura del **documento de rebaja** con el chatter estándar.
- Captura de la **consola** (sin `OwlError`) en cada caso.
- Opcional (si se conserva copia del estado anterior): `before`/`after` del chatter.

## Criterio de cierre

Los formularios de **Motonave**, **Viaje** y **documento de rebaja** abren sin `OwlError`; el chatter muestra
Mensajes/Seguidores estándar; **no** aparece «Agregar una línea»; **no** cambia ningún dato de negocio.

## Firma

| Fecha | Ejecutado por | Navegador / versión | Resultado global | Observaciones |
|---|---|---|---|---|
| | | | | |
