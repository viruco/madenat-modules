# Arquitectura — MADENAT Lumber Core

**Módulo:** `madenat_lumber_core`
**Versión documental:** `7.0.0`
**Fecha de actualización:** 2026-05-28
**Estado:** CANÓNICO — Fuente de verdad técnica
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
- `pieces`
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
- `lengthuom`
- `lengthinputraw`
- `vol_physical_m3`
- `vol_purchase_m3`
- `vol_shipment_m3`
- `vol_mbf`
- `export_calculation_rule`
- `audit_snapshot`
- `audit_hash`

### Nota crítica sobre largo
A partir del cambio documental del 2026-05-23 se consolida la política:
- `length` es la fuente de verdad en metros.
- `lengthinputraw` conserva el valor digitado por el operador.
- `lengthuom` define la unidad de entrada (`m`, `mm`, `ft`).
- La normalización debe ocurrir antes de cualquier cálculo volumétrico.

### Riesgo técnico vigente
✅ RESUELTO (23-mayo-2026) — el `@depends` de `_compute_lengthm` usa `lengthinputraw` y `lengthuom`, y el módulo actualiza sin error de registry.

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

El sistema opera bajo un flujo de tres compuertas lógicas:
1. **Gate 1 (Staging)**: Ingesta de datos desde Excel/PDF. Validación de tipos. Sin efectos en stock.
2. **Gate 2 (Verificación)**: Análisis comercial, nominales y tolerancias. Sin efectos en stock.
3. **Gate 3 (Validación)**: Generación de lotes (`stock.lot`) y movimientos. **Único punto autorizado de escritura en inventario**.

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