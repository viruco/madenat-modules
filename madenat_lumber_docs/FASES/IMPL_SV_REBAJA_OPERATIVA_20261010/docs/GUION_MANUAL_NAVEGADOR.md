# Guion manual de navegador (PENDIENTE) — «Rebaja de etiquetas» (operación y blindaje)

**Motivo:** no hay navegador real (Playwright/Selenium/Chromium) en el entorno. La verificación
*pixel* (**V3**) queda **pendiente**; **no** se sustituye por XML/ORM/SQL ni por pruebas.

**Entorno:** `madenat_test` · `http://localhost:8069`. Usuario con **Operaciones** (y **Jefatura**
para reversa).

**Registros de prueba:** una guía `service_return_confirmation='yes'` con ≥2 etiquetas de retorno. Si
no hay, usar una etiqueta SV existente (`SV00000000841`, id 10215) y una guía de retorno confirmada.

**Pasos**
1. **Logística Exportación → Rebaja de etiquetas**. El listado «Etiquetas SV» debe mostrar, sin
   truncar: Etiqueta SV, **N° Guía**, Proveedor, Producto, Volumen documental, Rebajado documental y
   Saldo documental. Probar el botón de columnas opcionales (Procesador, Fecha guía).
2. En el buscador, probar los filtros **Con saldo documental**, **Sin rebajas aplicadas**, **Con
   rebajas aplicadas**, **Sin saldo documental**, **Exceso documental** y (opcional) **En stock**.
   Comprobar que «En stock» **no** es condición y que el saldo documental ≠ stock.
3. Abrir una etiqueta SV → **Registrar rebaja**. En el selector «Guía de retorno» verificar que
   **sólo** aparecen guías confirmadas como retorno (y que el «Buscar más» no muestra No/vacías/
   canceladas). Si no aparece ninguna: mensaje «Seleccione una guía confirmada como retorno…».
4. Elegir la guía. Comprobar que **no** se incluye ninguna etiqueta automáticamente y que se ven
   **Nominal lote / Rebajado aplicado / Reservado / Disponible documental**.
5. Marcar un subconjunto (o «Seleccionar todas»). Comprobar el **Resumen documental** (seleccionadas,
   nominal incluido, reparto, **aplicado previo**, **disponible documental**) sin doble conteo.
6. En «Asignación a SV», asignar el SV de trabajo y el volumen. Probar **Guardar borrador** y
   **reabrir**: la selección y el reparto se conservan. Comprobar el mensaje «Actualiza el saldo
   documental SV. No mueve stock ni modifica el ledger SV».
7. **Aplicar** (Operaciones). Verificar actualización del saldo documental y ausencia de movimientos
   de stock. **Reversar** (Jefatura) y comprobar la historia.

**Registrar:** fecha, usuario, base, IDs y capturas. Cualquier diferencia → anotarla.
