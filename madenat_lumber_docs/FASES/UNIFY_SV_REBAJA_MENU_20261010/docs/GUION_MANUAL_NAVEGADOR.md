# Guion manual de navegador (PENDIENTE) — «Rebaja de etiquetas» (acceso unificado)

**Motivo:** no hay navegador real (Playwright/Selenium/Chromium) en el entorno. La verificación
*pixel* (**V3**) queda **pendiente** y **no** se sustituye por la comprobación de metadatos/SQL ni por
las pruebas transaccionales.

**Entorno:** `madenat_test` · `http://localhost:8069`. Usuario con **Operaciones** (y **Jefatura** para
reversa).

**Registros de prueba:** usar una etiqueta SV (`lot_flow_type='volume'`) con saldo documental. En la
base hay un SV de muestra `SV00000000841` (id 10215).

**Prueba principal:** «El usuario entra por UN SOLO enlace "Rebaja de etiquetas", registra una
asignación y consulta sus documentos e historia **sin** repetir la operación en otro menú».

**Pasos**
1. **Logística Exportación → Rebaja de etiquetas** (único enlace). Verificar que el listado se titula
   **«Etiquetas SV»** y muestra: etiqueta SV, guía de procedencia, producto, procesador, volumen
   documental, rebajado documental y saldo documental.
2. Confirmar que **no** existe (ni ha quedado) un segundo acceso «Asignaciones SV» ni
   «Imputaciones documentales SV» en el menú.
3. Probar la búsqueda: por **Etiqueta SV**, **Guía de procedencia** y **Producto**; comprobar que el
   filtro **«En stock»** es **opcional y removible** y que el listado también muestra SV sin
   existencia física (saldo documental ≠ stock).
4. Abrir una etiqueta SV. Comprobar el aviso «Esta operación registra asignaciones documentales de
   retornos a etiquetas SV. No genera movimientos de stock ni modifica el saldo del ledger SV.» y la
   lista de asignaciones con **Abrir documento**.
5. Pulsar **«Historial de rebajas»** → se abre el historial **de ese SV** (no crea nada). Volver al SV
   con el botón *Atrás*.
6. Pulsar **«Ver historial completo»** → se abren **todos** los documentos; comprobar los filtros
   **Vigentes** e **Históricos** (Borrador/Pendiente/Aplicada/Reversada/Anulada). Volver al SV.
7. Pulsar **«Registrar rebaja»** → asistente existente con el SV de trabajo cargado.
8. Elegir la guía, **Seleccionar todas** (o un subconjunto), editar el reparto y **Guardar borrador**.
   Reabrir: la selección y el reparto **se conservan**.
9. **Aplicar** (Operaciones). Comprobar el mensaje de efecto **documental** y que el SV actualiza
   **Rebajado documental**/**Saldo documental** (sin movimientos de stock).
10. Reversar (Jefatura); comprobar que el saldo documental vuelve y el documento queda **histórico**.
11. Confirmar que **no** hay que repetir la operación en otro menú y que **«Rebajar por Motonave»** y
    **«Consolidación»** no cambian.

**Registrar:** fecha, usuario, base, IDs y capturas. Cualquier diferencia → anotarla.