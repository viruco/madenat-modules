# Plan de despliegue ACUMULADO (PROPUESTO) — paquete pendiente para TEST remoto

**Estado:** **PREPARADO — NO EJECUTADO.** Requiere **autorización independiente de Mauricio**.
**El TEST remoto NO se toca en esta intervención** (Cristhian lo está usando con la **versión anterior**).

## 1. Paquete acumulado (versiones locales vigentes tras este hotfix)

| Módulo | Versión local vigente | Cambio en este hotfix |
|---|---|---|
| `madenat_lumber_logistics` | **18.0.1.26.0** | **Sí** — chatter `<chatter/>` en 2 formularios + prueba VIEW |
| `madenat_lumber_core` | 18.0.6.7.0 | No (arrastrado del WIP previo) |
| `madenat_lumber_intake` | 18.0.0.13.0 | No (arrastrado del WIP previo) |
| `madenat_lumber_costing` | 18.0.1.0.0 | No (arrastrado del WIP previo) |
| demás `madenat_*` | (versión instalada actual) | No |

## 2. Versión del TEST remoto

- **No inspeccionado** en esta intervención (regla: no tocar el TEST remoto). Se debe **leer en solo lectura**
  antes de desplegar (`SELECT name, latest_version FROM ir_module_module WHERE name LIKE 'madenat_%'`).
- Reporte operativo: Cristhian prueba la **versión anterior** ⇒ el TEST remoto **NO** tiene aún este hotfix
  (ni probablemente el chatter roto, que se reprodujo solo en **LOCAL**).

## 3. Causa de la inclusión
El formulario del documento `madenat.sv.imputation` (y el de `madenat.processor.return.link`) quedaban **sin
chatter** en Odoo 18 CE ⇒ listas o2m editables de `mail.message`/`mail.followers` con «Agregar una línea» y
`OwlError`. El paquete arrastra además el WIP previo de `core`/`intake`/`costing` (ya validado localmente).

## 4. Dependencias / migración
- **Sin** dependencias nuevas. Migración **aditiva** (solo arch de vistas). Sin script de datos.

## 5. Respaldos requeridos
`pg_dump -Fc <db>` · tar del filestore · copia de `madenat_lumber_logistics` (y de los demás módulos del
paquete). Respaldo local de esta intervención: `../code/pre_hotfix_db_madenat_test.sql.gz`,
`../code/pre_hotfix_logistics_module.tar.gz`, `../code/pre_hotfix_views.tar.gz`.

## 6. Comando de actualización (por módulo, **NUNCA** `-u all`)
```
odoo -d <db> -u madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics \
     --stop-after-init --no-http
```
Registrar versión, comando, `EXIT` y log.

## 7. Smoke test
1. Arranque sin `ERROR`.
2. Abrir `madenat.sv.imputation` (documento de PRUEBA, no `IMP04823`/`IMP02220`) ⇒ **sin** OwlError;
   **sin** «Agregar una línea» en Mensajes/Seguidores; historial visible.
3. Recorrido Guardar/Aplicar/Volver/Continuar/Anular/Reabrir/Reversar sin OwlError
   (guion `GUION_MANUAL_NAVEGADOR.md`).
4. Confirmar `latest_version` esperada.

## 8. Rollback
Restaurar el `pg_dump` previo + copia de los módulos + reiniciar.

## 9. Nota
El hotfix es **solo de vistas**. No cambia datos ni comportamiento de negocio. La aceptación en **navegador**
permanece **pendiente** (sin navegador en el entorno).

## 10. Árbol de decisión (a aplicar CUANDO llegue la salida de la inspección remota)

> Entrada: salida de `ALINEACION_DOC_Y_PRE_DESPLIEGUE_20261012/docs/INSPECCION_REMOTO_SOLO_LECTURA.sh`.
> **No** se decide sin evidencia. Cline **no** se conecta al remoto.

### CASO 1 — El remoto compila sólo `<chatter/>` y sus vistas MADENAT contienen `oe_chatter`
- **Diagnóstico:** defecto **presente** en TEST; Cristhian puede hallar el OwlError en esas pantallas.
- **Copiar:** `madenat_lumber_logistics` (18.0.1.26.0, con el fix del chatter).
- **Actualizar `-u`:** `madenat_lumber_logistics` (**no** `-u all`).
- **Respaldo previo:** `pg_dump -Fc <db>` + tar del filestore + copia del módulo.
- **Smoke test:** abrir `madenat.sv.imputation` (documento de PRUEBA) y `madenat.processor.return.link`;
  sin OwlError; chatter estándar (**sin** «Agregar una línea»); recorrido Guardar/Aplicar/Volver.
- **Rollback:** restaurar el `pg_dump` + copia del módulo + reiniciar.
- **Aviso a Cristhian:** ventana de pruebas interrumpida durante el `-u` (~minutos) + caché del navegador.
- **Prioridad:** **alta** (bug visible para el operador).

### CASO 2 — El remoto todavía compila `oe_chatter` (core antiguo)
- **Diagnóstico:** el defecto **no** se reproduce allí **por ahora**; pero el hotfix **sigue siendo necesario**
  antes de actualizar el core.
- **Copiar/actualizar:** igual que CASO 1, y **puede combinarse** con el paquete acumulado completo.
- **Respaldo/smoke/rollback:** igual que CASO 1.
- **Aviso:** coordinar con Cristhian; el cambio de core implica ventana mayor.
- **Prioridad:** **media** (preventiva).

### CASO 3 — `madenat_vendor_payment` instalado en el remoto con `oe_chatter` y build que no lo compila
- **Diagnóstico:** **riesgo adicional** (mismo defecto en otro formulario).
- **Propuesta (SUJETA A AUTORIZACIÓN):** corregir `views/lumber_shipment_cost_views.xml`
  (`div.oe_chatter` → `<chatter/>`). **Ojo:** el archivo **no está en el `data` del manifest** y el modelo
  `lumber.shipment.cost.line` **no** hereda `mail.thread` ⇒ si se habilita, además habría que (a) añadirlo al
  manifest y (b) dar soporte de chatter al modelo. **No** se ejecuta aquí.
- **Copiar/actualizar `-u`:** `madenat_vendor_payment` **sólo** si se autoriza la corrección anterior.
- **Prioridad:** **baja** (mientras el archivo siga huérfano no reproduce).

### CASO 4 — La versión remota de `core`/`intake`/`logistics` difiere de la asumida
- **Diagnóstico:** el paquete propuesto **no** aplica sin cambios.
- **Acción:** reconstruir el **paquete mínimo** y el **orden** de actualización según las versiones reales
  (evitar saltos no soportados; actualizar dependencias antes que dependientes: `core` → `intake` →
  `logistics`).
- **Respaldo/smoke/rollback:** iguales, con respaldo **obligatorio** antes de cualquier `-u`.
- **Prioridad:** **según brecha**; requiere nueva propuesta firmada.

### CASO 5 — Resultado incompleto o ambiguo
- **Acción:** **declarar PENDIENTE.** No decidir. Repetir la inspección con las correcciones indicadas por
  Mauricio (rutas de addons/log reales del remoto).

## 11. Pendientes de decisión de Mauricio (no se toman aquí)
1. `create` por RPC en `mail.message`/`mail.followers` (comportamiento estándar; **no** cambiar ACL).
2. Corrección de `madenat_vendor_payment` (CASO 3).
3. **Autorización** de despliegue al TEST remoto (ventana y aviso a Cristhian).
4. Límite ORM/RPC **sin** `edit_version` (ya declarado en LOCK V1).
5. Aceptación de Cristhian y evidencia de **navegador** (VIEW-01..07 cliente).
