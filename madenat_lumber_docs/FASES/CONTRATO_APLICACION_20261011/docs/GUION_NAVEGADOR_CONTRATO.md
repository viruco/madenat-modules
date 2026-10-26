# GUION DE ACEPTACIÓN EN NAVEGADOR — CONTRATO DE APLICACIÓN (A–I)

**Objetivo:** validar el ciclo real en la interfaz, con **registros de prueba** (no históricos).
**Entorno:** `madenat_test`, `http://localhost:8069`, contenedor `odoo18_app`.
**Estado:** **pendiente de Mauricio.** El entorno del agente **no tiene navegador**; este guion **no**
sustituye la aceptación y **no** se acredita con XML/ORM/SQL.

> Preparar **datos de prueba** (no documentos históricos): 1 guía de retorno
> (`¿Es retorno de servicio? = Sí`, no cancelada), 2 etiquetas procesadas con volumen nominal y **2 SV**
> con saldo documental positivo. Usuario con **Operaciones** (aplicar) y otro con **Jefatura** (revertir).

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| **A** | Logística → **Rebaja de etiquetas** → abrir una etiqueta SV → **Registrar rebaja** → elegir la guía de prueba. Reconocer el material (Etiqueta limpia · SKU · medidas · piezas · volumen documental). | Se listan las etiquetas de la guía, **sin selección automática**; cada fila muestra su **causa de saldo** y su disponible. |
| **B** | Marcar una etiqueta; en «A asignar (m³)» escribir una **cantidad parcial** (p. ej. 3 de 5). Revisar la columna **Pendiente de reparto**. | Se crea el reparto al SV de trabajo; **pendiente = 2 m³** (nominal 5 − reparto 3); el disponible de la etiqueta pasa a 0 (compromiso nominal). |
| **C** | **Guardar borrador**; cerrar y **reabrir** la operación. | El documento queda **Borrador**; al reabrir se **reconstruyen** selección y reparto; nada se aplicó. |
| **D** | **Dejar pendiente** (opcional) y luego **Revisar y aplicar** (usuario Operaciones). | Revisión muestra: **Nominal comprometido** ≠ **Repartido a SV** ≠ **Pendiente de reparto** ≠ **Efecto por SV**. Al aplicar, estado **Aplicada**, con usuario y fecha. |
| **E** | Abrir el **resultado persistente** (documento `IMP…`). | Se ve cabecera, líneas de etiquetas y reparto SV; accesible desde el SV («Historial de rebajas»). |
| **F** | Como **Jefatura**, pulsar **Reversar** escribiendo un **motivo**. | El documento pasa a **Reversada**; la etiqueta recupera su disponible; el original conserva líneas y reparto (historia append-only). Sin motivo **no** permite revertir. |
| **G** | **Reasignar**: nueva operación para la misma guía, reparto positivo y **Revisar y aplicar**. | Nuevo documento **Aplicada**; el anterior sigue **Reversada**; saldos coherentes. |
| **H** | Consultar **Historial de rebajas** y los saldos del SV. | Se ven ambos documentos (reversado + aplicado) y los saldos por SV cuadran con los repartos. |
| **I** | **Intentar aplicar sin reparto** (marcar una etiqueta y pulsar Revisar y aplicar sin asignar m³). | *(tras aprobar el contrato)* Mensaje: **«No se puede aplicar la rebaja: asigna una cantidad positiva a un SV. Puedes guardar el documento sin aplicarlo»**; el documento **no** se aplica y **no** consume capacidad. |

**Criterio de aceptación:** A–I sin errores de renderización; los mensajes y saldos coinciden con la
política. Registrar: usuario, fecha, documentos y capturas. Al completarse: **«Flujo aceptado por Mauricio»**,
con alcance y fecha.
