# Arquitectura — MADENAT Lumber Core

**Módulo:** `madenat_lumber_core`  
**Versión documental:** `6.0.0`  
**Fecha de actualización:** 2026-05-13  
**Estado:** ACTIVO — Arquitectura modular parcial, documentación alineada al estado real  
**Compatibilidad objetivo:** Odoo 18 CE

---

## 1. Propósito

Este módulo concentra el flujo operativo y técnico de MADENAT para recepción de madera, staging documental, análisis comercial, cálculo volumétrico, validación por gates y persistencia controlada a inventario.

Su responsabilidad principal no es solo “crear lotes”, sino garantizar que el paso desde documento origen hacia `stock.lot` ocurra con trazabilidad, consistencia matemática y control de side effects.

---

## 2. Posición en la cadena funcional

```text
madenat_lumber_shipping_core
            ↓
    madenat_lumber_core
            ↓
madenat_lumber_logistics / facturación futura
```

El módulo actúa como núcleo de ingestión, staging, validación y escritura controlada a stock.

---

## 3. Estado real de la arquitectura

La arquitectura actual es **modular parcial**. Esto significa que ya se extrajeron componentes importantes del antiguo monolito, pero todavía existe concentración funcional dentro de `models/lumber_reception.py`.

### Componentes desacoplados ya existentes
- `reception_parser.py` — Dispatcher y parseo multi-formato.
- `reception_workflow.py` — Flujo de estados y validaciones operativas.
- `reception_service.py` — Escritura a stock y servicios de persistencia.
- `mixin_lumber_ingest.py` — Lógica compartida de ingestión.
- `utils_uom.py` — Conversión y constantes volumétricas.
- `width_mapping.py` — Tabla de mapeo de anchos.

### Componente aún concentrado
- `models/lumber_reception.py` mantiene todavía:
  - `LumberReceptionLine`
  - `LumberReception`
  - computes de staging
  - parte de normalizaciones y comportamiento UI

**Conclusión arquitectónica:** el refactor estructural está avanzado y funcional, pero no está completada la separación total de línea/cabecera a archivos independientes.

---

## 4. Modelos funcionales principales

## 4.1 `lumber.reception.line`

Modelo de staging que representa la línea documental antes de Gate 3.

### Responsabilidades
- Reflejar la información cargada desde packing/documentos.
- Preservar triple capa: visual, física y nominal.
- Servir de superficie de corrección operativa previa a stock.
- Proveer base para cálculos de volumen y trazabilidad.

### Campos funcionales relevantes
- `reception_id`
- `lot_name`
- `package_no`
- `product_id`
- `subproduct_id`
- `product_code`
- `product_name`
- `pieces`
- `thickness_visual`
- `width_visual`
- `thickness`
- `width`
- `thickness_nominal`
- `width_nominal`
- `length`
- `length_uom`
- `length_input_raw`
- `vol_physical_m3`
- `vol_purchase_m3`
- `vol_shipment_m3`
- `vol_mbf`
- `export_calculation_rule`
- `audit_snapshot`
- `audit_hash`

### Nota crítica sobre largo
A partir del cambio documental del 2026-05-13 se consolida la política:
- `length` es la fuente de verdad en metros.
- `length_input_raw` conserva el valor digitado por el operador.
- `length_uom` define la unidad de entrada (`m`, `mm`, `ft`).
- La normalización debe ocurrir antes de cualquier cálculo volumétrico.

### Riesgo técnico vigente
Existe un hallazgo reciente que debe quedar trazado documentalmente: un `@depends` de `_compute_lengthm` sigue referenciando `lengthinputraw`, mientras el campo vigente documentado y esperado por vistas es `length_input_raw`. Esta discrepancia rompe la construcción del registry al instalar/actualizar el módulo y debe considerarse bug vivo de código, no de arquitectura.

---

## 4.2 `lumber.reception`

Cabecera del flujo de recepción.

### Responsabilidades
- Gestionar el estado del proceso.
- Orquestar gates y transiciones.
- Centralizar la recepción documental.
- Controlar cuándo una recepción puede procesarse, reabrirse o cancelarse.
- Vincular staging, snapshot y salida a inventario.

### Campos relevantes
- `reception_line_ids`
- `state`
- `ingestion_profile`
- `audit_snapshot`
- `audit_hash`
- `can_process_reception`
- `can_reopen_reception`
- `can_cancel_reception`
- `guia_numero`
- `guia_fecha`
- `supplier_id`
- `order_id`

---

## 4.3 `madenat.guia.processing` y líneas

Este flujo sigue siendo parte del módulo para escenarios de guía procesada, servicios y trazabilidad operativa complementaria.

### Responsabilidades
- Parsear guía de despacho.
- Integrar PDF y Excel.
- Crear staging alternativo.
- Validar consistencia.
- Transferir a stock cuando el flujo lo requiera.

---

## 5. Gates y política de side effects

## Gate 0
Validación básica de archivos y formato.  
**Regla:** no escribe stock.

## Gate 1
Conciliación documental PDF vs Excel vs OC.  
**Regla:** no escribe stock.

## Gate 2
Análisis comercial: producto, subproducto, nominales, tolerancias.  
**Regla:** no escribe stock.

## Gate 3
Snapshot final, firma SHA-256, commit de inventario y creación de lotes/movimientos.  
**Regla:** es el único punto autorizado para efectos reales en inventario.

---

## 6. Triple capa

La triple capa sigue siendo decisión estructural vigente:

- **Visual:** valor que vio el operador en el documento.
- **Física:** dato utilizable por backend y cálculos reales.
- **Nominal:** dato usado para costeo, compra y exportación.

Ninguna actualización funcional debe colapsar estas capas sin documentar la decisión.

---

## 7. Regla de largo y unidades

Se documenta formalmente la regla operativa para largo:

### Fuente de verdad
- `length` en metros.

### Campo de ingreso humano
- `length_input_raw`

### Selector semántico
- `length_uom`

### Conversión esperada
- `mm` → `length = length_input_raw * 0.001`
- `ft` → `length = length_input_raw * 0.3048`
- `m` → `length = length_input_raw`

### Implicación
Los cálculos de:
- `vol_physical_m3`
- `vol_purchase_m3`
- `vol_shipment_m3`
- `vol_mbf`

deben seguir leyendo `length` normalizado, nunca el campo crudo.

---

## 8. Relaciones con otros componentes

### Core Odoo
- `stock.lot`
- `stock.move`
- `stock.picking`
- `purchase.order`
- `product.product`
- `res.partner`
- `res.currency`
- `ir.attachment`

### Ecosistema MADENAT
- logística
- shipping
- futura integración financiera con consolidación de facturación

---

## 9. Estado de modularización

### Ya resuelto
- Parser desacoplado.
- Servicio de persistencia desacoplado.
- Helpers matemáticos desacoplados.
- Tabla de anchos separada.

### Pendiente
- Separación física de `LumberReceptionLine` hacia archivo propio.
- Adelgazamiento definitivo de `lumber_reception.py`.
- Cierre del bug de `@depends` inconsistente para largo.

---

## 10. Restricciones técnicas vigentes

- Odoo 18 CE.
- Uso de `<list>` en lugar de `<tree>` en vistas de lista.
- Sin SQL raw en producción.
- Sin fallback silencioso para tipo de cambio.
- Sin writes en Gate 0, 1 y 2.
- Documentar todo cambio estructural en `04_DECISION_LOG.md`.

---

## 11. Deuda técnica viva

| ID | Severidad | Descripción | Estado |
|---|---|---|---|
| DT-ARQ-01 | Alta | `lumber_reception.py` sigue concentrando demasiada lógica | Vigente |
| DT-ARQ-02 | Alta | Bug de `@depends` con `lengthinputraw` vs `length_input_raw` | Crítico |
| DT-ARQ-03 | Media | Constraint `stock_lot_check_cost_positive` falla en actualización | Vigente |
| DT-ARQ-04 | Media | Limpieza de warnings XML en vistas | Vigente |

---

## 12. Criterio de alineación documental

Este documento debe prevalecer sobre resúmenes antiguos.  
Si el código cambia en:
- layout de largo,
- campos de staging,
- gates,
- modularización,
- o política de side effects,

entonces este archivo debe actualizarse antes del siguiente commit.
