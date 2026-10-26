# Registro de incidencias de pruebas — Cristhian (TEST remoto)

**Regla:** **NO** se declara aceptación mientras no exista **resultado suyo**. Este archivo registra cada
incidencia recibida con los campos exigidos por la intervención. **No** se modifica el TEST remoto para
reproducir por conveniencia ni se despliega hotfix sin autorización independiente.

## Campos obligatorios por incidencia
| Campo | Contenido |
|---|---|
| Usuario / grupo | (p. ej. Cristhian — Operaciones / Jefatura) |
| Compañía | (compañía activa del usuario) |
| Versión remota | (módulo y versión desplegada, p. ej. `madenat_lumber_logistics 18.0.1.21.0`) |
| Recorrido | (pasos exactos: menú → acción → selección → Guardar/Aplicar) |
| Documento o registro | (referencia: `IMP…`, guía, etiqueta SV) |
| Resultado esperado vs real | (qué esperaba y qué ocurrió) |
| Captura / log | (adjunto o texto del error tal cual) |
| Reproducción local | (`madenat_test`: comandos/registros; **solo lectura** sobre datos reales) |
| Clasificación | **código** / **datos** / **permisos** / **interacción** |

## INC-2026-10-12-01 — «Listado remoto vacío» (etiquetas SV)
- **Usuario / grupo:** Cristhian — Operaciones.
- **Compañía:** (a confirmar con Cristhian).
- **Versión remota:** `madenat_lumber_logistics 18.0.1.21.0` (TEST remoto, **no modificado**).
- **Recorrido:** Logística → «Rebaja de etiquetas» (listado sobre `stock.lot`, etiquetas SV).
- **Documento o registro:** (sin referencia; listado vacío).
- **Resultado esperado vs real:** esperaba ver etiquetas SV elegibles; el listado apareció **vacío**.
- **Captura / log:** pendiente de captura del remoto (
  la petición de un FYI sin captura **no** permite confirmar el dominio aplicado).
- **Reproducción local:** **NO ejecutada sobre datos remotos.** Diagnóstico **de solo lectura** a realizar
  en local con datos equivalentes (§ abajo). **No** se crean ni modifican registros remotos.
- **Clasificación:** **datos / permisos** (a determinar).

### Diagnóstico de solo lectura recomendado (antes de crear o tocar registros)
Un listado vacío **NO** demuestra ausencia de etiquetas. Orden de comprobación (todo **lectura**):
1. **Dominio:** el listado «Etiquetas SV» filtra por `lot_flow_type = 'volume'`. Verificar si el usuario ve
   registros con ese tipo.
2. **Permisos / grupos:** comprobar que el usuario pertenece a un rol de Operaciones/Jefatura y que las
   reglas de registro (`ir.rule`) no excluyen las etiquetas por compañía.
3. **Compañía activa:** confirmar la compañía del usuario vs. la `company_id` de las etiquetas.
4. **Datos elegibles:** confirmar existencia de etiquetas SV (`lot_flow_type='volume'`) con saldo documental
   y su guía de retorno elegible (`service_return_confirmation='yes'`, no cancelada).
5. **Filtros de UI persistidos:** revisar filtros/agrupaciones por defecto que puedan ocultar filas.

> Estas comprobaciones son **de lectura**. Si el problema es de datos, se documenta y se decide **con
> autorización**; **no** se altera el remoto para «hacer aparecer» filas.

## Estado de aceptación
- **Aceptación:** **PENDIENTE** de resultado de Cristhian. No se afirma aceptación.
