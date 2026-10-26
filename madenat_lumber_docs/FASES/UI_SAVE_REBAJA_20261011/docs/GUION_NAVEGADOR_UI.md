# GUION DE ACEPTACIÓN EN NAVEGADOR — ACCIONES DEL ASISTENTE (UI)

**Objetivo:** comprobar que el recorrido real del SV permite guardar y mantener las rebajas **sin modo
desarrollador**. **Estado:** pendiente (el entorno del agente no tiene navegador).

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| A | Logística → **Rebaja de etiquetas** → abrir una **etiqueta SV** → **Registrar rebaja**. | Se abre el **formulario amplio** con **barra de acciones visible** (Guardar borrador · Revisar y aplicar · Descartar y volver). |
| B | Elegir guía; marcar etiquetas; **Preparar asignación**; escribir una **cantidad positiva**. | Filas preparadas; **aún no hay documento**. |
| C | Pulsar **Guardar borrador**. | Aparece **«Abrir documento»** y el mensaje **«Documento IMP… guardado (estado: draft). No se ha aplicado la rebaja…»**. Se **permanece** en el asistente. |
| D | Pulsar **Descartar y volver**. | Vuelve al **SV**; el borrador **sigue guardado**. |
| E | En el SV → **Trabajo en preparación** → **Continuar**. | Reabre el asistente con guía y SV precargados y **las mismas cantidades/destinos**. |
| F | Cambiar una cantidad y **Guardar borrador** otra vez. | **Mismo documento** (no duplica); mensaje con la **misma referencia**. |
| G | **Abrir documento**. | Se abre el documento persistente (`IMP…`) en Borrador. |
| H | **Revisar y aplicar** (con reparto positivo). | Se abre el documento en estado **Aplicada**; el SV muestra **«Rebajado documental»**. |
| I | **Revertir** con motivo (Jefatura). | Documento **Reversada**; historia conservada; el SV libera la capacidad. |
| J | **Reasignar**: nuevo borrador → guardar → aplicar. | **Nuevo** documento aplicado; el original permanece reversado. |
| K | **Cancelar** un borrador. | Estado **Anulada**; se libera la reserva; historia conservada. |

**Criterio de aceptación:** todas las acciones son **visibles y ejecutables** desde el recorrido del SV,
sin modo desarrollador; la referencia del documento se muestra al guardar; no se pierde ni duplica trabajo.
Al completarse: **«Flujo aceptado por Mauricio»**, con alcance y fecha.
