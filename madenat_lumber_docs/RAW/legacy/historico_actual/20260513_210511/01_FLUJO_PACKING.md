# MADENAT — Flujo Integral del Packing
**Versión:** 3.1.0  
**Fecha:** 2026-04-08  
**Estado:** ACTIVO 🟠

***

## 1. Objetivo

Controlar el recorrido completo de la información del packing desde la recepción documental hasta análisis comercial, muestra de exportación, bodega y auditoría, sin perder trazabilidad ni consistencia matemática.

***

## 2. Ruta canónica de información

```text
Recepción Física (Document Intake)
    ↓
Staging / Espejo Documental
    ↓
Análisis Comercial (Commercial Analysis)
    ↓
Muestra y Cálculo de Exportación (Export Sample)
    ↓
Bodega / Persistencia (Warehouse Persistence)
    ↓
Auditoría (Audit Trail)
```

***

## 3. Etapa 1 — Recepción Física

### Entradas
- PDF guía
- PDF OC (opcional)
- Excel Packing List

### Responsabilidades
- Validar archivos con Gate 0
- Parsear guía y OC
- Detectar layout del Excel
- Construir dict plano del parser
- Cruzar consistencia documental con Gate 1

### Resultado esperado
- Recepción en estado `verified`
- Líneas creadas en `lumber.reception.line`
- Sin stock creado aún

### Preguntas de control
1. ¿La guía existe y es válida?
2. ¿La OC coincide o está ausente pero justificada?
3. ¿El Excel fue reconocido como `Standard` o `Blanks`?
4. ¿El volumen declarado está dentro de tolerancia?
5. ¿El tipo de cambio vino del documento o fue digitado conscientemente?

***

## 4. Etapa 2 — Staging / Espejo Documental

### Propósito
Representar fielmente el contenido del packing antes de cualquier persistencia a stock.

### Qué debe mostrar la UI
- `package_no`
- `lot_name`
- `product_code`
- `product_name`
- `pieces`
- `thickness_visual`
- `width_visual`
- `thickness`
- `thickness_nominal`
- regla de exportación
- volúmenes por capa

### Reglas
- La capa visual debe conservar el valor del Excel.
- La capa física debe servir al backend.
- La capa nominal debe alimentar costeo/exportación.
- Si falta un valor crítico, el operador debe verlo antes de confirmar.

### Resultado esperado
- El usuario entiende exactamente qué llegó.
- Aún no se toca inventario.

***

## 5. Etapa 3 — Análisis Comercial

### Entradas
- Staging ya poblado
- Producto
- Subproducto
- Nominales
- Regla exportación

### Responsabilidades
- Validar catálogo comercial
- Validar producto activo
- Validar `tipo_subproducto`
- Completar y/o corregir nominales
- Reconciliar volúmenes recalculados
- Bloquear si Gate 2 falla

### Resultado esperado
- `vol_purchase_m3` confiable
- líneas comercialmente consistentes
- staging listo para snapshot

### Validaciones mínimas de Gate 2
- nominal no nulo
- nominal mayor a 0
- subproducto no nulo
- producto válido
- volumen recalculado dentro de tolerancia
- cero writes a stock

***

## 6. Etapa 4 — Muestra y Cálculo de Exportación

### Entradas
- Staging comercialmente aprobado
- Regla de exportación por línea
- Variables de dimensiones

### Responsabilidades
- Aplicar `metric`, `f1550` o `f5085`
- Calcular `vol_shipment_m3`
- Calcular `vol_mbf`
- Contrastar compra vs exportación
- Preparar información para reportes y embarque

### Resultado esperado
- La madera tiene una lectura exportable coherente
- La diferencia entre compra y embarque está explicada por la regla aplicada

### Punto de revisión
Si el volumen de exportación parece “bueno” pero no se puede reproducir matemáticamente, el flujo NO está cerrado.

***

## 7. Etapa 5 — Bodega / Persistencia

### Entradas
- Gate 3 aprobado
- snapshot SHA-256 válido

### Responsabilidades
- Crear `stock.lot`
- Crear `stock.picking`
- Crear movimientos de stock
- Vincular recepción y lotes
- Mantener trazabilidad por paquete

### Resultado esperado
- Estado `done`
- Existencia real en bodega
- Traza completa desde documento origen hasta lote final

### Restricción no negociable
Gate 3 es el único lugar que puede escribir stock.

***

## 8. Etapa 6 — Auditoría

### Qué se debe preservar
- número de guía
- OC
- usuario operador
- fecha/hora
- resumen de validación
- snapshot del staging
- hash SHA-256
- lotes generados
- picking generado

### Objetivo
Permitir reconstruir la historia de una recepción sin depender del relato humano.

***

## 9. Conciliaciones obligatorias

### 9.1. Recepción Física vs Staging
- cantidad de líneas
- `package_no`
- dimensiones originales
- volumen declarado

### 9.2. Staging vs Análisis Comercial
- producto
- subproducto
- nominales
- costo estimado
- volumen compra

### 9.3. Análisis Comercial vs Exportación
- regla aplicada
- volumen embarque
- MBF
- diferencias justificadas

### 9.4. Análisis Comercial vs Bodega
- `lot_name`
- producto
- piezas
- lotes creados
- picking generado

***

## 10. Casos típicos de error

| Problema | Señal | Acción |
| -------- | ----- | ------ |
| `package_no` no llega a lote | lote genérico o incorrecto | revisar `_fill_staging_table` |
| regla exportación errónea | volumen embarque inconsistente | revisar parser + `_compute_export_values()` |
| nominal faltante | Gate 2 bloquea | corregir análisis comercial |
| producto inválido | botón de confirmación debe bloquearse | revisar catálogo |
| T/C faltante | error financiero | ingreso manual obligatorio |

***

## 11. Evidencia mínima por recepción

- guía
- OC
- volumen PDF
- volumen Excel
- cantidad de líneas
- resultado Gate 1
- resultado Gate 2
- hash Gate 3
- cantidad de lotes creados
- picking generado

***

## 12. Definición de cerrado para este flujo

Se considera cerrado cuando:
- la ruta documental → comercial → exportación → bodega está descrita y validada,
- los cálculos se reproducen,
- las pruebas están registradas,
- la trazabilidad paquete → lote funciona,
- no hay side effects fuera de Gate 3.