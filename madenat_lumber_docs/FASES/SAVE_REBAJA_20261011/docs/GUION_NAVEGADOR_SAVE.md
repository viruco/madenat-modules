# GUION DE ACEPTACIÓN EN NAVEGADOR — PERSISTENCIA Y RECUPERACIÓN (SAVE)

**Objetivo:** Mauricio prepara el trabajo, lo **guarda explícitamente**, sale, lo **encuentra desde el SV**
y **continúa** con las mismas etiquetas, cantidades y destinos. **Registros de prueba** (no históricos).
**Estado:** pendiente (el entorno del agente no tiene navegador).

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| A | Logística → **Rebaja de etiquetas** → abrir una **etiqueta SV** (volumen) → **Registrar rebaja**. | Asistente abierto con el SV precargado; se pide la **guía** (retorno Sí). |
| B | Elegir la guía; marcar etiquetas; **Preparar asignación**; introducir **cantidad parcial** (p. ej. 4 de 10) en «A asignar (m³)». | Filas con el SV de trabajo; pendiente de reparto visible; **aún no hay documento**. |
| C | **Guardar borrador**. | Se abre el **documento persistente** (`IMP…`) en **Borrador**; referencia visible. |
| D | Salir al listado; abrir de nuevo la **etiqueta SV**. | En el formulario del SV aparece **«Trabajo en preparación»** con la referencia y **Continuar**; el listado muestra «Trabajo en prep.». |
| E | **Continuar** (o «Historial de rebajas»). | Asistente reabierto con **guía y SV precargados**; **mismas etiquetas, cantidades y destinos**. |
| F | Cambiar una cantidad y **Guardar borrador** de nuevo. | **Mismo documento** (no se duplica); valor actualizado. |
| G | Probar **cantidad 0** en una fila y guardar. | Guarda **sin error**; el destino previsto sin cantidad **no** se persiste como reparto; la etiqueta permanece. |
| H | **Revisar y aplicar** (con reparto positivo). | Pasa a **Aplicada**; el SV muestra «Rebajado documental»; **no** figura en «Rebaja doc.» un borrador. |
| I | **Revertir** con motivo y **reasignar**. | Revertida + nuevo borrador; historia consultable; sin pérdida ni duplicación. |

**Criterio de aceptación:** A–I sin errores; la referencia del documento guardado es visible; no depende
de conservar el asistente; borrador ≠ rebaja aplicada; sin pérdida ni duplicación silenciosa. Al
completarse: **«Flujo aceptado por Mauricio»**, con alcance y fecha.
