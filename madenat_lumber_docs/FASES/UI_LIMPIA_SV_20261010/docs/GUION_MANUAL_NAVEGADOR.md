# Guion manual de navegador (PENDIENTE) — «Registrar rebaja» (interfaz clara, ambas pestañas)

**Motivo:** no hay navegador real (Playwright/Selenium/Chromium) en el entorno. La verificación *pixel*
(**V3**) queda **pendiente**; **no** se sustituye por XML/ORM ni por pruebas. **No** se declara aceptación
visual.

**Entorno:** `madenat_test` · `http://localhost:8069`. Usuario con **Operaciones** (y **Jefatura** para
reversa).

**Registros de prueba:** una guía `service_return_confirmation='yes'` con ≥2 etiquetas de retorno (ideal:
etiquetas visibles repetidas con distinto largo). Si no hay, usar una etiqueta SV existente y una guía de
retorno confirmada.

**Pasos**

1. **Logística Exportación → Rebaja de etiquetas** → abrir una etiqueta SV → **Registrar rebaja**.
   Comprobar que el formulario abre **amplio** (no modal estrecho).
2. **Cabecera única:** SV de trabajo · Guía de retorno · **Saldo documental del SV** · **Seleccionadas** ·
   **Con reparto preparado** · **Preparado para el SV (m³)** · **Piezas de origen** · **Volumen documental
   de origen (m³)** · **Disponible documental (seleccionadas) (m³)**. Línea de resumen:
   «X seleccionadas · Y etiquetas con reparto preparado · Z m³ → <SV>». Comprobar el aviso «Rebaja
   documental: no mueve stock físico.».
3. **Materiales del retorno:** verificar columnas **Etiqueta** (limpia, sin nombre concatenado), SKU
   origen, Producto, Espesor (mm), Ancho (mm), Largo (m), Piezas, Vol. documental (m³), Disponible (m³) y
   **A asignar (m³)**. Comprobar que una **etiqueta repetida** aparece como dos filas distintas (por
   medidas) y que el texto de ayuda es una sola línea.
4. **Acciones:** «Seleccionar todas» (sólo marca; si hay filas sin disponibilidad, aparece el aviso con
   cuántas no son asignables), «Quitar selección», **«Preparar asignación»** (tooltip: «Prepara el reparto
   al SV de trabajo; no aplica la rebaja») y **«Usar disponible»** (mismo alcance en ambas pestañas).
5. **Editar «A asignar» en la propia tabla** (caso de un solo SV, sin cambiar de pestaña). Comprobar que el
   resumen y la cabecera se actualizan y que **«Usar disponible» no sobrescribe** una cantidad ya escrita.
6. **Asignación a SV:** comprobar que con un solo SV la tabla es **Etiqueta · Medidas · Disponible (m³) ·
   A asignar (m³)** y que el SV destino está en la cabecera. Si se prepara reparto hacia un **segundo SV**,
   comprobar que aparece la columna **«SV destino»** y que el subtotal del SV de trabajo se separa del
   total general.
7. **Guardar borrador** y reabrir: selección y reparto se conservan. **Revisar y aplicar** (Operaciones) →
   sin movimientos de stock. **Reversar** (Jefatura) → historia intacta.
8. **Fila con disponible 0,000:** abrir la columna opcional «Estado disponibilidad» y comprobar que indica
   la causa real (Aplicado / Reservado / Sin capacidad documental) y que **no** se ofrece como asignable.

**Registrar:** fecha, usuario, base, IDs y capturas de **ambas pestañas**. Cualquier diferencia → anotarla
(no declarar aceptación sin la revisión de Mauricio).
