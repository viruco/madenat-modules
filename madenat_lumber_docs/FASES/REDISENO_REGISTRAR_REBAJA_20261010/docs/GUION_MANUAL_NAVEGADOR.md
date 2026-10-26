# Guion manual de navegador (PENDIENTE) — rediseño del asistente «Registrar rebaja»

**Motivo:** no hay navegador en el entorno. **V3 *pixel* pendiente**; esta es la revisión de aceptación
de **Mauricio**.

**Entorno:** `madenat_test` · `http://localhost:8069`. Usuario **Operaciones**.
**Registros:** guía **19827** (17 etiquetas de retorno) y **SV00000000841**. Sólo inspección; no
aplicar sobre históricos.

**Pasos**
1. **Logística Exportación → Rebaja de etiquetas** → abrir SV00000000841 → **Registrar rebaja**.
   Comprobar que se abre como **formulario amplio** (no modal estrecho).
2. Cabecera: SV, guía, **saldo documental del SV**, seleccionadas, total preparado y resumen.
3. Elegir la guía **19827**. En «Materiales del retorno» verificar columnas legibles sin truncar:
   **Etiqueta · SKU origen · Producto · Espesor · Ancho · Largo · Piezas · Volumen documental ·
   Disponible · Cantidad preparada**.
4. Comprobar etiquetas repetidas (p. ej. D7719, D7670, D7721) en **filas distintas** con distinto
   largo/SKU (no agrupadas).
5. Activar/desactivar columnas opcionales (Subproducto, Lote interno, declaradas, avanzadas) y probar
   el desplazamiento horizontal.
6. **Seleccionar todas** (sólo marca; no asigna). Luego **Asignar seleccionadas al SV de trabajo**
   (crea filas con volumen 0 en «Asignación a SV»). Introducir un volumen o **Usar disponible**.
7. Comprobar **Cantidad preparada** por fila y el resumen «X etiquetas · Y m³ preparados para SV…».
8. **Guardar borrador** y reabrir: selección, cantidades y reparto se conservan. Los botones
   «Proponer FIFO (propuesta)» y «Dejar pendiente» deben verse con menor jerarquía.

**Registrar:** fecha, usuario, base, IDs y capturas. Cualquier diferencia → anotarla.
