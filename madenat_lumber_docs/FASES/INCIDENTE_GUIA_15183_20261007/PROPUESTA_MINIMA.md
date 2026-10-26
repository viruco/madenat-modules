# PROPUESTA MÍNIMA — control de guía ya ingresada (staging/cabecera, cross-model)

> Sólo **propuesta**. No se implementa ni despliega. No se toca CANON ni datos.

## A. Objetivo del control

Detectar una **guía ya ingresada** antes de duplicar sus efectos, **aunque esté en
staging y sin stock**, y **sin** usar el modelo distinto como exclusión automática
ni bloquear números homónimos legítimos. Identidad = **`name` (número) + emisor**.

## B. Punto único de intervención

`madenat_lumber_core/models/reception_parser.py` → `_check_guide_duplicate`
(`:32-189`), reutilizado por ambos flujos. No se añade modelo, campo, ACL, índice
ni `sudo` nuevo.

## C. Cambio mínimo (dos partes)

**C.1 — Comparar por identidad (emisor) en la búsqueda de Recepción.**
Hoy la rama de `lumber.reception` busca sólo por `name` + `company` (`:96-98`). Se
añade el **emisor** cuando se conoce, para que una coincidencia cross-model exija
**mismo proveedor**:

```python
reception_domain = [('name', '=', guide_no)]
if 'company_id' in reception_model._fields:
    reception_domain.append(('company_id', '=', company_id))
if partner_id:                              # emisor conocido → identidad completa
    reception_domain.append(('supplier_id', '=', partner_id))
```
La rama de `madenat.guia.processing` **ya** filtra por `partner_id` (`:150-151`).

**C.2 — Habilitar el alcance cruzado en las llamadas de BLOQUEO.**
En los llamadores de bloqueo (no en los de aviso), usar `cross_model=True` y pasar
el **emisor** cuando se conoce:

| Llamador | Hoy | Propuesto |
|---|---|---|
| `madenat_guia_processing._check_guide_identity_duplicate` (`:3358`) | `cross_model=False` | `cross_model=True` (ya pasa `partner_id`) |
| `madenat_guia_processing._check_guide_identity_duplicate_on_create` (`:3404`) | `cross_model=False` | `cross_model=True` (ya pasa `partner_id`) |
| `reception_workflow._check_duplicate_and_warn` (`:276`) | `cross_model=False` | `cross_model=True`, pasando `partner_id=reception.supplier_id.id or None` |

Regla de seguridad: **el bloqueo cross-model exige identidad completa
(emisor conocido).** Si el emisor aún se desconoce → **no** se bloquea cross-model
(se conserva la captura; AJUSTE A se mantiene). Así no se bloquea ni un número
homónimo de emisor distinto ni una captura incompleta.

## D. Conflicto doctrinal (expreso)

- **Postura A (ALINEADA con el incidente):** la identidad documental es
  `número + emisor`; el mismo documento no debe ingresarse dos veces por otro flujo.
  El control debe usar el **número para detectar** y el **emisor para confirmar**.
- **Postura B (base del AJUSTE B previo):** `CANON/12 §5.2` prohíbe usar
  `guia_number` como **discriminador de origen de lotes**; `FIX_GUIA_DUP_CIERRE`
  lo extendió a «el número no bloquea entre flujos» y llevó `cross_model=False`.

**El conflicto es real y se identifica sin reinterpretar CANON:** §5.2 regula el
**discriminador de reportes/lotes**, no prohíbe **detectar** un documento ya
ingresado. La postura A **no** usa `guia_number` como discriminador de origen: usa
`recepción_id`/`guia_processing_id` (intactos) y añade una **detección de duplicado
por identidad** en la ingesta. La postura B **sobre-extiende** §5.2. **Requiere
ratificación del Arquitecto** (cambio de política del AJUSTE B, no cosmético).

## E. Cumplimiento de restricciones

| Restricción | Cumple |
|---|---|
| Sin nueva arquitectura | ✅ (sólo comparación y un argumento) |
| Sin bloquear homónimos legítimos (emisor distinto) | ✅ (filtro por emisor) |
| Sin impedir captura incompleta | ✅ (AJUSTE A: sin emisor no bloquea cross-model) |
| Sin depender de stock | ✅ (busca cabeceras) |
| Sin usar el modelo distinto como exclusión automática | ✅ (`cross_model=True` en bloqueo) |
| Sin fusionar/borrar históricos | ✅ (no toca datos) |
| No toca CANON/ACL/XML | ✅ (sólo `models/`) |

## F. Impacto y riesgo

- **Efecto:** una segunda cabecera del **mismo documento** por otro flujo se
  **bloquea** con el mensaje existente de C1 (N°, proveedor, fecha, estado, ID).
- **Riesgo:** falso bloqueo si el emisor se resuelve de forma distinta entre
  flujos (p. ej. RUT equivalente en dos `res.partner`). Mitigación: comparar por
  `partner_id` resuelto; considerar comparación por RUT si se desea (fase 2).
- **No cambia:** Recepción→Recepción (mismo modelo, ya bloquea por `name`),
  homónimos de emisor distinto, captura incompleta, relectura propia
  (`exclude_id`/`exclude_model`).

## G. Verificación (aislada)

- Las pruebas `R1`/`R2` de `PRUEBA_REGRESION_…` **deben pasar** tras el cambio.
- `E1` y `NG1` **deben seguir pasando** (no sobre-bloqueo).
- Ejecutar la suite existente `TestGuideDuplicateIngest` revisando
  `test_03`/`test_28`: su expectativa actual (**no bloquear** el mismo emisor
  cross-model) **contradice** el requisito del incidente y debe **actualizarse**
  a homónimo de **emisor distinto** (no al mismo emisor).

---

## Cierre (recordatorio)

> La intervención mínima propuesta es comparar por **identidad (`name` + emisor)**
> a través de **ambos** flujos en el **punto único**
> `madenat_lumber_core/models/reception_parser.py::_check_guide_duplicate`
> (+ `cross_model=True` en los llamadores de bloqueo), manteniendo el aviso
> no bloqueante para homónimos de emisor distinto.
