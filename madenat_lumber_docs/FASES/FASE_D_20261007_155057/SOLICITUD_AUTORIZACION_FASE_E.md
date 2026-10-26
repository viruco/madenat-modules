# SOLICITUD DE AUTORIZACIÓN — FASE E (eliminación definitiva)

> **Borrador para aprobación.** **NO** es una autorización y **no** se ejecuta todavía.
> Requiere, además, la **evidencia de pantalla de la Fase D** (ver `GUION_VERIFICACION_PANTALLA.md`).

## Datos de la operación

| Campo | Valor |
|---|---|
| Base | **`madenat_test`** (desarrollo local) |
| Servicio | `odoo18_app` |
| Ruta UI | Intake → **Ciclo de vida de la guía** → **A. Eliminar definitivamente** → **Ejecutar** |
| Guía | **`madenat.guia.processing` ID 33152 · número 15183** |
| Estado | `cancelled` · tipo `service` |
| Diagnóstico | `REQUIREMENTS_OK_A = True`, **0 bloqueadores**, 0 documentos propios, 0 ambiguos |
| Documento ajeno | `EMB-00227` (picking 436, recepción 1369) — **no** bloquea, **no** se toca |

## Motivo propuesto (trazable)

> "Eliminación de ingreso cancelado sin operaciones materiales propias, tras reparación
> autorizada del vínculo incorrecto del retorno 7813. Referencia:
> `FIX_DELETE_INTAKE_20261007_145130 / FASE_E`."

## Tratamiento de mensajes y adjuntos

- Se eliminan con la guía: **5 `mail.message`** y **4 `ir.attachment`**.
- El evento firmado **`guia_delete_permanent`** (`madenat.audit.log`) preserva metadatos de
  **4 mensajes** (excluye el aviso de creación) y **2 adjuntos de chatter**.

## Limitación del snapshot (reconocimiento EXPRESO)

> **Los dos documentos de campo binario — `guide_pdf_file` y `excel_file` (adjuntos 65071 y
> 65072) — NO quedarán conservados por el snapshot de eliminación.** El snapshot registra
> solo los adjuntos visibles por el ORM (chatter), no los de campo binario. Al autorizar la
> Fase E se **reconoce expresamente** esta limitación. La recuperación de estos binarios,
> si se requiriera, solo es posible por **restauración completa** del respaldo protegido.

## Respaldo y límites de recuperación

- Ubicación protegida: `backups/FASE_B_20261007_153214/` (permisos `700`).
- Contenido: `madenat_test.dump` (`-Fc`), `filestore_madenat_test.tar.gz`, código/config.
- Cobertura verificada por lectura de contenido: guía + los 4 adjuntos (2 archivos físicos,
  sha256 tar ↔ volumen idénticos).
- **Límite:** `git apply -R` **no** revierte la operación; el retorno al estado previo exige
  **restaurar dump + filestore**. **No** se ha probado una restauración.
- La reparación previa del FK queda registrada en `madenat.audit.log` id 21739
  (vínculo `ondelete='set null'` → **sobrevive** al borrado).

## Intacto tras la operación (no se modifica)

- **Recepción 1369** y su material.
- **Cadena 436 → 7813 → 7814** (pickings y movimientos 6420/14542/14543).
- Lotes 2614–2625 (recepción 1369), stock, valoración y contabilidad.

## Solicitud

> **¿Autorizas eliminar definitivamente la guía `madenat.guia.processing` ID 33152 / número
> 15183 desde el asistente "Ciclo de vida de la guía" — Modo A — en `madenat_test`, con el
> tratamiento documental descrito, reconociendo expresamente que los documentos de campo
> binario (`guide_pdf_file`, `excel_file`) no quedarán conservados por el snapshot, y
> manteniendo intactas la recepción 1369 y la cadena 436→7813→7814?**

## Condición previa a la ejecución

La autorización debe ir acompañada de la **evidencia de pantalla de la Fase D** (quién
verificó, fecha, N° de bloqueadores = 0, ausencia de `EMB-00227` como bloqueador, captura).
Sin esa evidencia no se procede.
