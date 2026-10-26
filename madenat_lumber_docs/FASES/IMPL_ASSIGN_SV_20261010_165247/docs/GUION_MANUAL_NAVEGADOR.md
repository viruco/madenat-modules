# Guion manual de navegador (PENDIENTE) — Asignaciones SV centradas en SV

> **⚠ INSTRUCCIÓN DE MENÚ SUPERADA (2026-10-10).** El acceso **«Logística Exportación →
> Asignaciones SV»** de este guion es **histórico**: fue sustituido por el **único** acceso
> **«Logística Exportación → Rebaja de etiquetas»** al unificar la navegación (ver
> `FASES/UNIFY_SV_REBAJA_MENU_20261010/docs/GUION_MANUAL_NAVEGADOR.md` y `CANON/19` §19.15). El resto del
> procedimiento (pasos 2–12) sigue siendo válido; sólo cambia el rótulo del punto de entrada. Se
> conserva este documento como **antecedente**; no se borra la historia.

**Motivo:** no hay navegador real (Playwright/Selenium/Chromium) en el entorno. La
verificación *pixel* (**V3**) queda **pendiente** y **no** se sustituye por la comprobación
de integración web/RPC (que solo acredita menú visible y `default_get`).

**Entorno:** `madenat_test` · `http://localhost:8069`. Usuario con **Operaciones**.

**Registros de prueba:** usar una guía de retorno marcada «retorno de servicio = Sí» con ≥2
etiquetas y ≥1 SV (`lot_flow_type='volume'`). En la base hay un SV de muestra `SV00000000841`
(id 10215).

**Prueba principal:** «Un SV recibe algunas etiquetas de la guía A y otras de la guía B,
mediante dos imputaciones manuales visibles desde el mismo SV».

**Pasos**
1. **Logística → Asignaciones SV**: verificar que el listado muestra sólo SVs (Lote Volumen)
   con su guía de procedencia, nominal, total imputado aplicado y saldo documental I2.
2. Abrir un SV: comprobar el aviso «La imputación no modifica stock ni saldo del ledger SV» y
   el detalle de asignaciones (imputación, guía, etiqueta, volumen, estado, fecha, usuario).
3. **Asignar retorno** (cabecera): el asistente abre con el **SV de trabajo** cargado y **sin
   guía** y **sin etiquetas** (no auto-inclusión).
4. Elegir **Guía A** manualmente. Comprobar que aparecen las etiquetas **sin** marcar.
5. **Seleccionar todas** (o marcar un subconjunto). Editar el nominal si procede.
6. En **Asignación a SV**, añadir el SV de trabajo y el volumen (≤ nominal de la etiqueta).
7. **Guardar borrador** → reabrir el asistente para la misma guía: la **selección y el reparto
   se conservan** (no se recarga la guía).
8. **Aplicar** (Operaciones). Comprobar el mensaje de efecto documental y que el SV muestra el
   total imputado aplicado actualizado.
9. Repetir con **Guía B** y el **mismo SV**: debe crear un **segundo documento**; el SV debe
   listar **dos asignaciones** (una por guía) sin duplicar.
10. Reversar una imputación (usuario **Jefatura**): el saldo documental I2 vuelve; la
    procedencia del vínculo envío–retorno se conserva (vigencia = revertida).
11. Intentar forzar una **etiqueta ajena a la guía** (otra guía) → debe **rechazarse**.
12. Forzar **reparto > nominal** → debe **rechazarse**. Reparto **parcial** → admitido.

**Registrar:** fecha, usuario, base, IDs y capturas. Cualquier diferencia → anotarla.
