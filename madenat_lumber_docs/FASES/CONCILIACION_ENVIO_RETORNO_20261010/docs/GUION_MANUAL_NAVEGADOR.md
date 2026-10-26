# Guion manual de navegador (PENDIENTE) — Bloques A/B/C + ajuste de integridad

**Motivo:** no hay navegador en el entorno (Playwright/Selenium/Chromium ausentes). Esta verificación
queda **pendiente** y **no** se sustituye por integración web/RPC ni por lectura de `get_views`.

**Entorno:** `madenat_test` · `http://localhost:8069`. Usuarios: uno con **Operaciones** y otro con
**Jefatura de Operaciones**.

**Registros de prueba (identificados):** procesador `V3 Planta (temp)` (14785) · guía `V3-CONCIL`
(33737) · envío picking `7973` · relación `REL00030` (estado `reversed`).

**Pasos**
1. Abrir la guía de retorno (33737) → pestaña «Conciliación Envío–Retorno».
2. Botón «Imputación documental SV» → asistente.
3. Pestaña «Envíos a procesador (retorno)»: seleccionar el envío elegible (7973).
4. Completar etiquetas/SV → **Aplicar**. Observar badge **Vigencia documental = Imputación vigente**.
5. Consultar el vínculo en guía, picking e imputación.
6. **Reversar la imputación** (usuario Jefatura). Comprobar: **procedencia** sigue «Conciliación
   registrada» (`linked`) y **Vigencia documental** = «Imputación revertida (requiere reimputación)».
7. **Reimputar:** abrir de nuevo el asistente, aplicar una nueva imputación. Comprobar que el vínculo
   apunta a la nueva y que «Imputación reemplazada» conserva la anterior, **sin** fila activa duplicada.
8. Revisar listas: **sin totales duplicados** de volúmenes (sin sumatorios); badge de vigencia visible.
9. Forzar una selección incompatible (envío no elegible) → debe **rechazarse**.

**Registrar:** fecha, usuario, base, IDs de los registros y capturas. Cualquier diferencia → anotarla.
