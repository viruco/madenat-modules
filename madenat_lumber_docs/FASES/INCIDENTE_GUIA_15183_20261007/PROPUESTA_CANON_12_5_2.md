# PROPUESTA DE INTERPRETACIÓN — `CANON/12 §5.2` (para ratificación documental)

> **Propuesta. NO se edita CANON.** Este documento se somete a ratificación; una vez
> aprobado, el CANON se actualizará en una entrega documental separada.

## 1. Texto vigente (resumen fiel)

`CANON/12 §5.2` (Prohibiciones): «**No usar `guia_number` como discriminador.**
`guia_number` es un campo informativo/computado y no es confiable para distinguir
origen.» Y §5.1 fija los discriminadores válidos de origen de lote:
`reception_id` (recepción directa) y `guia_processing_id` (guía procesada).

## 2. Lectura corregida (propuesta)

`§5.2` regula **cómo se discrimina el ORIGEN de un lote en reportes y consultas**
(por `reception_id` / `guia_processing_id`), **no** la **detección de un documento
ya ingresado** durante la ingesta. Son dos planos distintos:

| Plano | Regla |
|---|---|
| Discriminación de origen (reportes/lotes) | **Intacta**: `reception_id` / `guia_processing_id`. El número **no** discrimina origen. |
| Detección de duplicado en la ingesta | El número **puede** usarse para **detectar** coincidencias **siempre** combinado con la **identidad del emisor conocida**. |

**Identidad documental = `número + emisor`.**
- Mismo número **y mismo emisor** conocido ⇒ **mismo documento** ⇒ **bloquear**
  (aunque esté en staging, sin stock, o venga por otro flujo/modelo).
- Mismo número **y emisor distinto** (o emisor desconocido) ⇒ **homónimo legítimo**
  ⇒ **no bloquear** (aviso no bloqueante).

Esto **no** usa `guia_number` como discriminador de origen; reutiliza el número
sólo como **clave de detección** confirmada por el emisor. El origen sigue
resolviéndose por las FK canónicas.

## 3. Texto propuesto para `CANON/12 §5.2` (adenda)

> **5.2.b Detección de duplicado en la ingesta (ingreso de madera).**
> El número de guía **no** discrimina origen, pero **sí** se usa —combinado con el
> **emisor conocido**— para **detectar un documento ya ingresado**. Si el número y
> el emisor coinciden con una cabecera existente (en `lumber.reception` **o** en
> `madenat.guia.processing`), se considera el **mismo documento** y la segunda
> ingesta se **bloquea**. Si el emisor es **distinto** o **se desconoce**, la
> coincidencia es un **homónimo**: no se bloquea (se advierte; la captura
> incompleta se conserva y se revalida al completar la identidad). La detección
> **no** depende de la existencia de stock.

## 4. Conflicto y su resolución (expreso)

- El cierre previo `FIX_GUIA_DUP_CIERRE_20261007_170340` (AJUSTE B) llevó
  `cross_model=False` **citando `§5.2`**. Se identifica como **sobre-extensión**:
  `§5.2` prohíbe el número como **discriminador de origen**, no como **clave de
  detección**.
- El incidente (Procesado 15183 sobre Recepción 15183, **mismo emisor**) demuestra
  la brecha: el documento ya ingresado **no** fue bloqueado.
- **Resolución propuesta:** adoptar la lectura de §2/§3 (identidad = número +
  emisor) y **corregir AJUSTE B**; requiere un **AD nuevo** en
  `CANON/04_DECISION_LOG.md` que reemplace la justificación de simetría.

## 5. Alcance de la ratificación

- No reescribe `§5.1` ni los discriminadores de origen (intactos).
- No crea unicidad global por número (los homónimos de **emisor distinto** siguen
  permitidos; existen casos legítimos, p. ej. `CANON/12 §6.2`).
- No cambia estados, staging, lotes ni reportes.

## 6. Estado

**Pendiente de ratificación por el Arquitecto / Tech Lead.** Hasta entonces, la
implementación propuesta (`RESULTADOS_IMPLEMENTACION.md`) se mantiene **en
aislamiento** y **no** se despliega.
