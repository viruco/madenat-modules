# Guion manual de navegador (PENDIENTE) — «Seleccionar todas» y asignación explícita

**Motivo:** no hay navegador real (Playwright/Selenium/Chromium) en el entorno. La verificación
*pixel* (**V3**) queda **pendiente**; **no** se sustituye por XML/ORM/RPC ni por pruebas.

**Entorno:** `madenat_test` · `http://localhost:8069`. Usuario con **Operaciones**.

**Registros de prueba:** guía **19827** (17 etiquetas, retorno confirmado) y un SV existente
(`SV00000000841`).

**Pasos**
1. **Logística Exportación → Rebaja de etiquetas** → abrir un SV → **Registrar rebaja**.
2. Elegir la **guía 19827** (sólo deben aparecer retornos confirmados).
3. Pulsar **«Seleccionar todas»** **sin guardar antes**. Comprobar que **no** aparece el error de
   `processed_lot_id` y que quedan marcadas todas las etiquetas.
4. Confirmar que la tabla muestra **Etiqueta proveedor / Lote interno / Disponible para esta
   operación / Nominal comprometido** (y columnas opcionales con las secundarias).
5. Ir a **«Asignación a SV»** → **«Asignar seleccionadas al SV de trabajo»**. Comprobar que se crea
   una fila por etiqueta con **volumen 0** y el SV de trabajo.
6. Escribir un volumen (o pulsar **«Usar disponible»**) y ver el resumen **«X etiquetas · Y m³
   preparados para SV…»**.
7. **Guardar borrador** y **reabrir**: la selección, las cantidades y el reparto se conservan.
8. Comprobar el mensaje «Actualiza el saldo documental SV. No mueve stock ni modifica el ledger SV».

**Registrar:** fecha, usuario, base, IDs y capturas. Cualquier diferencia → anotarla.
