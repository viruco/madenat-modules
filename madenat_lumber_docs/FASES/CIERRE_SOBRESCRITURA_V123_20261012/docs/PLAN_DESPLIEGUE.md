# Plan de despliegue PROPUESTO — CIERRE V1–V3 (LOCK) 18.0.1.25.0

**Estado:** **PREPARADO — NO EJECUTADO.** Requiere **autorización independiente de Mauricio**.
**El TEST remoto permanece estable para Cristhian; NO se despliega en esta intervención.**

## 1. Módulos (lista exacta)
- `madenat_lumber_logistics` **18.0.1.25.0** (único con cambios).
- `madenat_lumber_core` **18.0.6.6.0** — sin cambios (debe estar instalado).

## 2. Dependencias / migración
- Sin dependencias nuevas. Migración **aditiva**: columna `edit_version` (`default=1`) + `force_save` en la vista
  del formulario. Sin script de datos.

## 3. Respaldos requeridos
`pg_dump -Fc <db>` · tar del filestore · copia del módulo `madenat_lumber_logistics`.

## 4. Comando de actualización (LOCAL)
```
odoo -d <db> -u madenat_lumber_logistics --stop-after-init --no-http
```
**No** `-u all`. Registrar versión, comando, `EXIT` y log.

## 5. Smoke test
1. Arranque sin `ERROR`/`inconsistent`/`should be searchable`.
2. `edit_version` presente (default 1).
3. Recorrido Guardar/Aplicar/Volver.
4. **Edición directa:** abrir el documento en dos pestañas; en una guardar; en la otra (obsoleta) guardar ⇒
   **mensaje de conflicto**; «Recargar versión actual» reconstruye.
5. **V2 (cliente):** ejecutar el guion `docs/GUION_V2_CLIENTE.md` y adjuntar capturas.
6. Confirmar `latest_version = 18.0.1.25.0`.

## 6. Rollback
Restaurar `<db>_pre_lock.dump` + copia del módulo + reiniciar.

## 7. Nota
`edit_version` aditivo; los documentos existentes quedan en `1` y suben al primer guardado. La protección de la
edición directa depende de que el cliente envíe `edit_version` (cliente Odoo estándar con `force_save`); el guion
V2 lo confirma.
