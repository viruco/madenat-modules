# Guion manual de navegador (PENDIENTE) — HOTFIX OwlError «Registrar rebaja»

**Motivo:** no hay navegador real (Playwright/Selenium/Chromium) en el entorno. La comprobación de
**renderización** del cliente Owl queda **pendiente**; **no** se sustituye por XML/ORM ni por pruebas.

**Entorno:** `madenat_test` · `http://localhost:8069`. Usuario con **Operaciones**.

**Resultado esperado general:** el asistente **abre y renderiza** sin `EvalError` / `OwlError`.

**Pasos**

1. **Logística Exportación → Rebaja de etiquetas** → abrir una etiqueta SV → **Registrar rebaja**.
   - **Caso A:** apertura **sin líneas de reparto**. No debe aparecer `OwlError`/`EvalError`. La pestaña
     «Asignación a SV» no debe mostrar la columna «SV destino».
2. **Caso B:** preparar reparto **sólo al SV de trabajo** («Preparar asignación» + «Usar disponible»).
   La columna **«SV destino»** debe permanecer **oculta**; el reparto del SV de trabajo no se pierde.
3. **Caso C:** añadir reparto hacia un **segundo SV**. La columna **«SV destino»** debe aparecer y mostrar
   los destinos correctos por fila.
4. **Caso D:** volver a **un solo SV** (quitar el reparto adicional) y de nuevo a varios. La visibilidad
   debe actualizarse **sin errores** y **sin perder** los repartos existentes.
5. **Caso E:** **Guardar borrador** y **reabrir** el asistente. La selección, el reparto, los totales de
   cabecera y la **visibilidad** (columna «SV destino») deben **conservarse** correctamente.
6. Comprobar en consola del navegador que **no** aparece
   `Can not evaluate python expression: (bool(not wizard_id.multi_sv))`.
7. **Aplicar** (y **Reversar** con Jefatura) para confirmar que no hay efectos físicos.

**Registrar:** fecha, usuario, base, IDs y capturas de **cada caso (A–E)**. Cualquier diferencia →
anotarla. **No** declarar aceptación sin la revisión de Mauricio.
