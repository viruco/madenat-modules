# GUION DE ACEPTACIÓN EN NAVEGADOR — VOLVER A BORRADOR (RESET)

**Objetivo:** cancelar una rebaja, reabrirla con motivo, corregir/reasignar y Guardar o Aplicar, en la
misma ventana. **Estado:** pendiente (sin navegador en el entorno del agente).

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| A | SV → **Registrar rebaja** → guía → etiquetas → m³ → **[Guardar]**. | Borrador `IMP…` visible; mensaje con la referencia. |
| B | **Abrir documento** (Más opciones) → **[Anular]**. | Documento **Anulado**; se registran usuario/fecha/motivo. |
| C | Volver al asistente (o reabrirlo). | Aparece **[Volver a borrador]** y el aviso «Documento anulado… reabrir vuelve a activar las reservas previstas»; **no** se ofrecen Guardar/Aplicar. |
| D | Escribir el **Motivo de reapertura** y pulsar **[Volver a borrador]**. | Mensaje «Documento IMP… reabierto como borrador…»; se reconstruyen etiquetas y reparto; vuelven **[Guardar] [Aplicar]**. |
| E | Corregir cantidades y/o destinos; **[Guardar]**. | Mismo documento (sin duplicar); reservas de borrador restablecidas. |
| F | **[Aplicar]**. | Rebaja aplicada una sola vez; resultado visible; tablas en sólo lectura. |
| G | Consultar el documento → pestaña **Motivo / Reversa**. | Se ven **Anulada por/fecha/motivo** y **Reabierta por/fecha/motivo**; la referencia es la misma. |
| H | Intentar **[Volver a borrador]** sobre un **aplicado**. | No se ofrece la acción; la corrección es por **reversa**. |

**Criterio de aceptación:** una rebaja cancelada vuelve explícitamente a borrador (permisos, capacidad y
coherencia), se corrige/reasigna y se Guarda o Aplica; la cancelación permanece en la historia. Al
completarse: **«Flujo aceptado por Mauricio»**, con alcance y fecha.
