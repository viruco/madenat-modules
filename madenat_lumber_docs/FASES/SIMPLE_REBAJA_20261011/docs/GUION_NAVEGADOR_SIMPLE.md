# GUION DE ACEPTACIÓN EN NAVEGADOR — RECORRIDO SIMPLIFICADO (SIMPLE)

**Objetivo:** en la **misma ventana**, seleccionar material → indicar m³ → **Guardar** o **Aplicar**.
**Estado:** pendiente (sin navegador en el entorno del agente).

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| A | Logística → **Rebaja de etiquetas** → abrir una **etiqueta SV** → **Registrar rebaja**. | Formulario amplio con **botonera de tres acciones**: **[Guardar] [Aplicar] [Volver]**. Sin pasos «Preparar». |
| B | Elegir la guía; marcar una o varias etiquetas; escribir los **m³ a rebajar** en la tabla **Materiales**. | El m³ editado define el reparto hacia el SV de trabajo; el disponible se actualiza. |
| C | Pulsar **[Aplicar]** (sin Guardar previo). | Mensaje **«Rebaja IMP… aplicada · X,XXX m³ hacia SV…»**; estado aplicado; saldo actualizado; **no** se abre otro formulario; las tablas quedan bloqueadas. |
| D | Abrir otra etiqueta SV → elegir guía → marcar etiquetas → m³ → **[Guardar]**. | Mensaje **«Borrador IMP… guardado…»**; se permanece en la ventana; **Abrir documento** (en «Más opciones») disponible. |
| E | **[Volver]** (pide confirmación si hay cambios sin guardar). | Regresa al **SV**; el borrador guardado **sigue**. |
| F | En el SV → **Trabajo en preparación** → **Continuar**. | Reabre la ventana con guía, etiquetas y **m³** precargados; mismo documento. |
| G | **[Aplicar]** desde el asistente reabierto. | Aplica sin abrir el documento; resultado en la misma ventana. |
| H | Intentar **[Aplicar]** con **0 m³**. | Mensaje **«Indica los m³ a rebajar en las etiquetas seleccionadas.»**; no aplica. |
| I | Intentar **[Aplicar]** con etiquetas **sin disponibilidad**. | Mensaje **«Las etiquetas seleccionadas no tienen disponibilidad…»**; no aplica. |
| J | **Más opciones (avanzado)** → Abrir documento / Dejar pendiente / Proponer FIFO. | Disponibles como opciones secundarias; **no** son requisito para Guardar/Aplicar. |

**Criterio de aceptación:** Mauricio selecciona, indica m³ y pulsa **Guardar** (para continuar) o
**Aplicar** (para ejecutar), sin etapas adicionales. Al completarse: **«Flujo aceptado por Mauricio»**,
con alcance y fecha.
