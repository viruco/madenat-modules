# Plan de despliegue PROPUESTO — BLINDAJE DE BORRADORES (LOCK) 18.0.1.24.0

**Estado:** **PREPARADO — NO EJECUTADO.** Requiere **autorización independiente de Mauricio**.
**El TEST remoto permanece estable para Cristhian; NO se despliega en esta intervención.**

## 1. Módulos a desplegar (lista exacta)
- `madenat_lumber_logistics` **18.0.1.24.0** (único módulo con cambios).
- `madenat_lumber_core` **18.0.6.6.0** — **sin cambios** (solo debe estar instalado).

## 2. Dependencias
- Odoo 18.0 CE; PostgreSQL; `madenat_lumber_core` (mixin, grupos, guía). Ninguna dependencia nueva.

## 3. Respaldos requeridos (antes de actualizar)
- **Base de datos** objetivo: `pg_dump -Fc <db> > <db>_pre_lock.dump`.
- **Filestore**: tar del `filestore/<db>`.
- **Código**: copia del módulo `madenat_lumber_logistics` vigente.

## 4. Comprobaciones previas
- `git rev-parse HEAD` y rama esperados; módulo `madenat_lumber_core` `installed`.
- `madenat.sv.imputation` sin documentos en estado inválido; sin `-u all`.
- Ausencia de cambios de esquema destructivos: la migración es **aditiva** (columna `edit_version`).

## 5. Comando de actualización (LOCAL — ejemplo)
```
odoo -d <db> -u madenat_lumber_logistics --stop-after-init --no-http
```
**No** `-u all`. Registrar versión, comando, `EXIT` y log.

## 6. Smoke test (post-actualización)
1. Log de arranque sin `ERROR`/`inconsistent`/`should be searchable`.
2. `madenat.sv.imputation`: `edit_version` presente (default 1) en documentos existentes.
3. Recorrido: seleccionar material → m³ → **Guardar** → documento persistido; **Aplicar** sin Guardar previo.
4. Concurrencia: dos sesiones sobre el mismo borrador ⇒ la segunda (versión obsoleta) recibe el **mensaje de
   conflicto**; «Recargar versión actual» reconstruye.
5. Confirmar `madenat_lumber_logistics` `latest_version = 18.0.1.24.0`.

## 7. Plan de rollback
1. Detener servicio.
2. Restaurar la base desde `<db>_pre_lock.dump` (`pg_restore`).
3. Restaurar el código de `madenat_lumber_logistics` (copia previa).
4. Reiniciar; verificar versión y arranque.

## 8. Nota sobre `edit_version`
Campo **aditivo** con `default=1`. Odoo lo inicializa al actualizar el módulo; **no** requiere migración de
datos ni script. Los documentos existentes quedan en `edit_version = 1` y suben al primer guardado.
