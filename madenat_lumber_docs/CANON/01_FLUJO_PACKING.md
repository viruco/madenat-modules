# MADENAT — Flujo Integral del Packing

**Versión documental:** 4.0.0
**Fecha de actualización:** 2026-05-13
**Estado:** ACTIVO — Validado conceptualmente, con incidencia técnica viva en largo/unidades

---

## 1. Objetivo

Controlar el recorrido completo del packing desde documento origen hasta lote final, preservando trazabilidad, cálculos reproducibles y control estricto sobre el momento en que se escribe inventario.

---

## 2. Ruta canónica

```text
Recepción Física
    ↓
Gate 0
    ↓
Gate 1
    ↓
Staging / Espejo Documental
    ↓
Gate 2 / Análisis Comercial
    ↓
Cálculo Exportación
    ↓
Gate 3 / Snapshot + SHA-256
    ↓
Persistencia a Stock
    ↓
Auditoría
```

---

## 3. Etapa 1 — Recepción Física

### Entradas
- PDF guía
- PDF OC (opcional)
- Excel packing list

### Objetivo
Confirmar que existe base documental suficiente y legible para construir staging.

### Salida esperada
- Recepción reconocida.
- Archivos cargados.
- Ningún write real a stock.

---

## 4. Etapa 2 — Gate 0

### Qué valida
- Formato de archivo
- tamaño
- integridad mínima
- posibilidad de parseo

### Regla
Gate 0 no puede dejar efectos secundarios de inventario.

---

## 5. Etapa 3 — Gate 1

### Qué valida
- guía vs Excel
- guía vs OC
- tipo de cambio
- volumen declarado
- consistencia documental mínima

### Salida esperada
- recepción verificada
- líneas de staging creadas
- bloqueo si existe inconsistencia crítica

---

## 6. Etapa 4 — Staging / Espejo Documental

El staging es un espejo controlado del documento y no una aproximación libre.

### Debe exponer
- `package_no`
- `lot_name`
- producto
- subproducto
- piezas
- capa visual
- capa física
- capa nominal
- regla de exportación
- volúmenes

### Regla nueva de largo
El operador puede ingresar largo en:
- metros
- milímetros
- pies

pero el sistema debe convertir siempre a metros internos.

### Campos asociados
- `lengthinputraw`
- `lengthuom`
- `length`

### Riesgo operativo
Si el largo se ve correcto en UI pero el compute está dependiendo de un campo inexistente, la instalación del módulo se rompe antes de que el flujo pueda validarse. Por eso cualquier inconsistencia en `lengthinputraw` impacta el flujo completo.

---

## 7. Etapa 5 — Análisis Comercial / Gate 2

### Valida
- producto activo
- subproducto válido
- nominales presentes
- volumen recalculado en tolerancia
- coherencia comercial del staging

### Restricción
No puede crear stock.

### Salida esperada
- staging listo para snapshot
- línea aprobable
- diferencia compra/embarque entendible

---

## 8. Etapa 6 — Cálculo de exportación

### Reglas vigentes
- `metric`
- `f1550`
- `f5085`
- perfiles adicionales según negocio

### Objetivo
Obtener volumen exportable reproducible matemáticamente.

### Regla de oro
Si un valor “parece correcto” pero no puede reproducirse, el flujo no está cerrado.

---

## 9. Etapa 7 — Gate 3

### Requisitos
- staging validado
- snapshot completo
- hash SHA-256
- autorización para persistencia

### Único lugar con write real
Gate 3 crea:
- `stock.lot`
- `stock.move`
- `stock.picking`
- vínculos de trazabilidad

---

## 10. Etapa 8 — Auditoría

### Evidencia mínima
- guía
- OC
- Excel
- usuario
- timestamp
- resumen de validaciones
- snapshot
- hash
- lotes creados
- picking creado

### Meta
Reconstruir una recepción sin depender de memoria humana.

---

## 11. Conciliaciones obligatorias

### 11.1 Documento vs staging
- líneas
- dimensiones
- package
- volumen

### 11.2 Staging vs análisis comercial
- producto
- subproducto
- nominales
- tolerancias

### 11.3 Análisis comercial vs exportación
- regla aplicada
- volumen salida
- MBF
- diferencia explicada

### 11.4 Exportación vs stock
- lot_name
- piezas
- lotes creados
- picking creado

---

## 12. Casos de error típicos

| Problema | Síntoma | Acción |
|---|---|---|
| `package_no` no propaga | lote genérico | revisar staging y servicio |
| Regla exportación mal aplicada | volumen incoherente | revisar compute |
| Nominal faltante | Gate 2 bloquea | corregir staging |
| Producto inválido | no debería confirmar | revisar catálogo |
| Tipo de cambio ausente | error financiero | bloquear |
| `lengthinputraw` en depends | falla registry | corregir código y actualizar pruebas |

---

## 13. Definición de cerrado

El flujo se considera realmente cerrado cuando:
- la ruta documental → staging → análisis → exportación → stock está trazada,
- los cálculos se reproducen,
- Gate 3 es el único write real,
- y la política de largo/unidades queda estable en código, vistas, tests y documentación.
