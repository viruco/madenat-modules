# GUION DE VERIFICACIÓN EN NAVEGADOR — A/B Retorno de servicio + UI de Ingreso de Madera

> **Estado: NO EJECUTADO.** Quien suscribe **no dispone de navegador**; por tanto esta verificación
> **no se declara completada**. Requiere que la realice una persona con navegador.

## Entorno (2026-10-08) — **desarrollo existente**

| Dato | Valor |
|---|---|
| **URL** | `http://localhost:8069/` |
| **Base de datos (desarrollo)** | `madenat_test` |
| **Usuario** | `cristhian.elguetag@gmail.com` (uid 8; **sin `sudo`**; sus grupos **no** se modifican) |
| **Servicio** | contenedor `odoo18_app` (imagen `odoo-18-ce-web:latest`) |
| **Código cargado** | `custom_addons` montado en `/mnt/extra-addons` (A/B **y** ajuste de UI **aplicados**) |
| **Registro de prueba sugerido** | guía **19827** (id 1198; `tipo_recepcion='service'`, `state='verified'`; fila de consola `processed` con `service_return_in_scope=True` y confirmación **vacía**) |

> **Nota (2026-10-08).** El **aislamiento temporal A/B** (`srvretab_web` en `127.0.0.1:8070`, base
> `srvretab_gate_20261007`, volumen `srvretab_web_data`, `/tmp/gate`, `/tmp/ab_dryrun`, `/tmp/iso_*`) se
> **retiró** tras verificar la implementación; sus dumps se conservan en
> `APPLY_AB_UI_20261008/retired/db/`. **Este guion se ejecuta íntegramente sobre `8069` /
> `madenat_test`.** No se conservan ni divulgan credenciales de aquel aislamiento.
>
> **Si un paso de la interfaz no permite volver a vacío** (dejar el radio sin selección), registrar el
> defecto y resolverlo **dentro del alcance**; **no** sustituir la evidencia de navegador por
> escrituras SQL.

Notas de alcance:
- No se envía a stock ninguna guía existente sólo para completar una casilla de verificación.
- Las acciones que cambian datos se hacen sobre registros identificados como pruebas de desarrollo.
- Se registra **fecha, usuario, base, registro, resultado y captura** por cada comprobación.

## Pasos

1. Abrir `http://localhost:8069/` → iniciar sesión (usuario de arriba). **No** usar `sudo` ni modificar
   grupos.
2. **Menú:** *Ingreso de Madera* (Consola de Intake).

### A. Reorganización de la interfaz (2026-10-08)

- **UI-1 — Resumen del ingreso en DOS columnas:** columna izquierda *Producto · Fecha de guía ·
  Proveedor · Procesador*; columna derecha *OC documental · OC vinculada · Estado de OC · Referencia*.
  Sin campos duplicados.
- **UI-2 — «Aplicar cambios»** ubicado **debajo** de los campos, conservando su acción y su condición
  de visibilidad (no visible en estados `sent`/`cancel`/`error`).
- **UI-3 — «¿Es retorno de servicio?»** en una **línea completa** debajo de ambas columnas, con las dos
  opciones (Sí / No) en la misma línea.
- **UI-4 — Evidencia documental en TRES columnas** y con **un solo** encabezado: 1) Documentos
  (Guía PDF, Packing list Excel); 2) Volúmenes y diferencias; 3) Packing y conciliación.
- **UI-5 — Detalle del packing list** debajo de Evidencia documental y a **todo el ancho**.
- **UI-6 — Responsive:** estrechar la ventana; las columnas deben reacomodarse sin romper la pantalla y
  los nombres largos de adjuntos **no** deben superponerse a las otras columnas.

### B. Identificación de retorno de servicio (alcance A)

- **A-1 (visibilidad):** en un ingreso **Procesado de servicio** (*Tipo de Recepción = Servicio
  Externo*) debe verse el control; en Producto/Volúmenes/compra **no** debe aparecer.
- **A-2 (Sí persiste):** seleccionar **Sí** → guardar → reabrir → debe conservar **Sí**.
- **A-3 (No persiste):** seleccionar **No** → guardar → reabrir → debe conservar **No**.
- **A-4 (vacío persiste):** dejar **sin selección** → guardar → reabrir → debe quedar **vacío**
  (*pendiente*, ≠ No). Si la interfaz **no permite volver a vacío**, registrar el defecto (no usar SQL).
- **A-5 (no bloquea):** con el campo vacío, el ingreso debe **poder** continuar/enviarse a stock; el
  error, si lo hay, debe ser de **otra** índole, **nunca** «Antes de enviar a stock, indique si este
  ingreso es un retorno de servicio». **No** enviar a stock una guía real sólo para esta comprobación.
- **A-6 (sin imputación automática):** marcar **Sí** **no** debe crear ninguna imputación SV.

### C. Imputación documental SV (alcance B)

- **B-1:** el **borrador/pendiente** de una imputación se guarda **sin** exigir que el destino esté
  marcado **Sí**.
- **B-2:** **Aplicar** con la guía destino en **No** o **vacío** devuelve el **rechazo** previsto.
- **B-3:** **Aplicar** con la guía destino en **Sí** funciona cuando se cumplen los demás requisitos.
- **B-4:** con una imputación **aplicada**, cambiar la identificación a **No** (o vaciarla) es
  **rechazado**.
- **B-5:** **reversar** la imputación con un usuario autorizado **permite** luego el cambio, si el
  estado de la guía lo admite.

### D. Usuario real

- Repetir A y C con el **usuario real Cristhian** (permisos reales, `su=False`). **No** modificar sus
  grupos ni otorgar privilegios nuevos.

## Criterio de cierre

Marcar como **verificado** sólo si A-1..A-6, B-1..B-5 y UI-1..UI-6 se observan **en navegador** y se
registran fecha, usuario, base, registro, resultado y captura en `03_TESTS.md` §12.6.
**Hasta entonces, la verificación en navegador (V3) queda PENDIENTE.**

## Entorno temporal retirado (2026-10-08)

El aislamiento A/B ya **no** existe: `srvretab_web` (stop + rm), volumen `srvretab_web_data`, bases
`srvretab_gate_20261007` / `srvretab_base_20261007` / `srvretab_test_20261007` y
`/tmp/{gate,ab_dryrun,iso_*}` **eliminados**. Dumps de las tres bases conservados en
`APPLY_AB_UI_20261008/retired/db/`. **No** recrear el aislamiento para ejecutar este guion.

## Captura del OwlError (P0 / R15) — paso manual (2026-10-10)

El cliente web puede fallar al abrir un formulario con
`OwlError: TypeError: Cannot read properties of undefined (reading 'includes')`
en `Many2OneField` (`get urlRelation`). **No reproducido** en el entorno de
trabajo (sin navegador). Para cerrar R15 se requiere **una** captura:

1. Navegador en `http://localhost:8069`, base `madenat_test`, **usuario no
   administrador** (sin `sudo`, sin ampliar permisos).
2. Reproducir el mismo menú/acción/registro del reporte (Mauricio).
3. Capturar: **URL completa** · pestaña **Console** (traceback Owl completo, con
   el nombre del **modelo y campo** resaltados) · pestaña **Network** (última
   petición `/web/dataset/...`).
4. Registrar fecha, usuario, base y registro; adjuntar la captura.

Diagnóstico estático ya descartado (0 campos `many2one` sin `relation`; 0 JS
propio que altere `Many2OneField`; 0 incidencias en logs):
`02_CONTINUIDAD.md` §17.16.1. Sin esa captura, R15 permanece **abierto**.
**No** borrar assets ni parchear el JavaScript global.

