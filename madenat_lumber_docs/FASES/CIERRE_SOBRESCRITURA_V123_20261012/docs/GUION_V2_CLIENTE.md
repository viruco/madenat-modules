# V2 — GUION DE EVIDENCIA DE CLIENTE (navegador) — PENDIENTE

**Estado:** **PENDIENTE — NO EJECUTADA.** No hay navegador ni herramienta de automatización utilizable en el
entorno local (sin `chromium`/`chrome`/`firefox`/`chromedriver`/`geckodriver`/`playwright`/`selenium`). **No se
sustituye** esta evidencia por ORM/XML y **no se fabrican capturas**.

**Ejecutar por:** Mauricio / Cristhian (o quien disponga de navegador sobre el entorno LOCAL `madenat_test`).

## Recorrido (dos pestañas/sesiones)
Preparar: una guía de retorno elegible con su etiqueta y un SV; abrir el asistente «Registrar rebaja».

1. **Pestaña A** y **Pestaña B**: abrir el **mismo borrador** (misma guía) — vía «Registrar rebaja» sobre el SV.
2. En **A**: seleccionar material → indicar m³ → **Guardar**. (No cerrar A.)
3. En **B**: modificar cantidades/selección **sin guardar**.
4. Pulsar **Guardar** en **B**.
5. **Capturar** el mensaje emergente (texto exacto).
6. **Verificar** si las cantidades locales de **B** siguen **visibles** tras el rechazo.
7. **Verificar** que el documento (Abrir documento / historial) conserva los datos de **A**.
8. Pulsar **«Recargar versión actual»**.
9. **Confirmar** el diálogo de descarte («Se descartarán los cambios NO guardados…»).
10. **Verificar** que se muestran los datos **vigentes** (los de A).
11. Editar en B y **Guardar** de nuevo → debe funcionar **sin** falso conflicto.

**Repetir** los pasos 2–11 para: **Aplicar** (en A) y **Dejar pendiente** (en A).

## Verificaciones adicionales
- **Cancelar** el diálogo de recarga → no debe descartar ni recargar; sin cambios persistentes.
- **Cerrar la ventana** tras el conflicto → el documento persistente queda igual (datos de A).
- `expected_edit_version` se actualiza **sólo** al recargar o tras una operación exitosa.
- El rechazo **no** deja el asistente aparentando éxito (sin `save_result`/`apply_result` de éxito).
- **No** se crea documento duplicado (un solo documento por guía).
- **No** se muestran datos de documentos ajenos.

## Evidencia a aportar
- Captura del mensaje de conflicto (paso 5).
- Captura del estado de **B** tras el rechazo (paso 6: ¿conserva las cantidades locales?).
- Captura del documento tras el rechazo (paso 7: datos de A intactos).
- Captura tras la recarga (paso 10) y del guardado exitoso posterior (paso 11).
- Navegador y versión usados; hora; usuario(s); compañía.

## Qué debe informarse como resultado
- **Mensaje:** ¿coincide con el operativo (sin error técnico PG)?
- **Cambios locales:** ¿se conservan en pantalla o se descartan? (Si se descartan, diagnosticar si es
  comportamiento estándar de Odoo; si no puede conservarse sin otra persistencia, ajustar el mensaje.)
- **Confirmación de recarga:** ¿aparece y descarta correctamente?
- **Sin duplicado / sin fuga:** confirmado.

> **Nota ORM (no sustituye lo anterior):** `LOCK-14` acredita a nivel ORM que el rechazo **no** adopta la versión
> ajena en silencio; la conservación de las ediciones **en el navegador** sólo la prueba esta V2.
