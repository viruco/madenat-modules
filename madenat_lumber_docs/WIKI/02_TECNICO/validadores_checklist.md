# Validadores de Integridad — ValidationChecklistMixin

**Módulo:** `madenat_lumber_core.models.validation_checklist_mixin`  
**Clase:** `ValidationChecklistMixin`  
**Versión:** 1.0.0  
**Última actualización:** 2026-06-02  
**Responsable:** Validación transversal de integridad

---

## Propósito

El `ValidationChecklistMixin` proporciona 7 validadores de negocio que garantizan la integridad de datos a través del pipeline de ingesta. Cada validador:
- Ejecuta una única responsabilidad
- Registra su resultado en `validation.checklist.item` (auditoría)
- Puede ser bloqueante (`is_blocking=True`) o informativo
- Soporta múltiples contextos (recepciones, guías de procesamiento, etc.)

---

## Arquitectura

```
ValidationChecklistMixin (AbstractModel)
├── _validate_uom_consistency()           ← UOM de productos
├── _validate_volumes_positive()          ← Volumen > 0
├── _validate_no_duplicate_lots()         ← No duplicados (30 días)
├── _validate_patio_capacity()            ← Capacidad patio
├── _validate_product_configuration()     ← Configuración Odoo 18
├── _validate_toll_processing_genealogy() ← Genealogía (canal procesado)
└── _validate_purchase_order_exists()     ← OC (canal bruto)

        ↓ (todos escriben en)

ValidationChecklistItem (Model)
├── reception_id o guia_id
├── check_type (tipo de validador)
├── status: failed | passed
├── is_blocking
├── message (user-facing)
└── details (técnico)
```

---

## Validador 1: _validate_uom_consistency()

**Responsabilidad:** Garantizar que todos los productos de lotes usen UoM = m³

### Lógica

1. Obtiene referencia de UOM `uom.product_uom_cubic_meter`
2. Filtra lotes cuyo producto tenga `uom_id ≠ m³`
3. Si hay incidencias:
   - Registra resultado como **FAILED** con detalles
   - Recomienda 3 soluciones operativas
   - Establece `is_blocking=True`
4. Si pasa:
   - Registra resultado como **PASSED**
   - Cuenta total de lotes validados

### Resultado

```python
validation.checklist.item {
    'check_type': 'uom_consistency',
    'status': 'failed' | 'passed',
    'is_blocking': True,
    'message': "❌ 3 lotes tienen productos con UoM incorrecta" | "✅ Todos tienen m³",
    'details': [Lote L-001: UoM 'kg' (debe ser 'm³'), ...],
    'suggested_fix': "Corregir UoM en Inventario > Productos | Script SQL | Reemplazar productos"
}
```

### Casos de fallo

| Caso | Causa | Impacto |
|---|---|---|
| Producto con UoM 'kg' | Error de catálogo | Conversión volumétrica imposible |
| Producto con UoM 'pcs' | Migración incompleta | Cálculos fracasan |
| Lote sin producto asignado | Datos incompletos | No puede validarse |

### Soluciones operativas (suggested_fix)

1. **Corregir manualmente en Inventario > Productos**
   - Acceso: Ajustes > Unidades de Medida
   - Acción: Cambiar UoM a m³

2. **Ejecutar script SQL de migración**
   - Para migraciones masivas de UoM
   - Requiere DBA

3. **Reemplazar productos por versión corregida**
   - Si producto es obsoleto
   - Crear versión nueva con UoM correcta

---

## Validador 2: _validate_volumes_positive()

**Responsabilidad:** Garantizar que todos los lotes tengan volumen de compra > 0

### Lógica

1. Itera cada lote de la recepción/guía
2. Valida `volume_purchase_m3 > 0` (volumen nominal que va a stock)
3. Si hay lotes con volumen ≤ 0:
   - Registra **FAILED**
   - Establece `is_blocking=True` (crítico)
   - Recomienda reingresar dimensiones
4. Si todos son positivos:
   - Registra **PASSED**

### Blindaje Regla de Oro

⚠️ **IMPORTANTE:** Valida el volumen **que irá a STOCK** (nominal/compra), no el volumen de embarque.
- Volumen nominal (`volume_purchase_m3`) ← **Validado aquí**
- Volumen embarque (`vol_shipment_m3`) ← Derivado, validarse en lógica de cálculo

### Resultado

```python
validation.checklist.item {
    'check_type': 'volumes_positive',
    'status': 'failed' | 'passed',
    'is_blocking': True,
    'message': "❌ 2 lotes tienen volumen ≤ 0" | "✅ Todos tienen volumen > 0",
    'details': [Lote L-001: 0.000 m³, Lote L-002: -0.050 m³],
    'suggested_fix': "Verificar dimensiones ingresadas (espesor, ancho, largo) y reingresar"
}
```

### Causas raíz de fallo

| Causa | Lote afectado | Solución |
|---|---|---|
| Dimensión faltante (0 mm/m) | Cualquiera | Reingresar desde Excel/PDF |
| Error de parsing | Blanks o especiales | Verificar formato entrada |
| Validación insuficiente en staging | Múltiples | Revisar parsing de recepción |

---

## Validador 3: _validate_no_duplicate_lots()

**Responsabilidad:** Evitar lotes duplicados dentro de 30 días

### Lógica

1. Para cada lote en recepción/guía:
   - Obtiene `lot_name` (código único)
   - Busca lotes con mismo nombre creados en últimos 30 días
   - Excluye lote actual de búsqueda

2. Si encuentra duplicado:
   - Registra **WARNING** (no bloqueante)
   - Recomienda acción: revisar o reutilizar lote
   - Muestra fecha del lote anterior

3. Si no hay duplicados:
   - Registra **PASSED**

### Resultado

```python
validation.checklist.item {
    'check_type': 'no_duplicate_lots',
    'status': 'warning' | 'passed',
    'is_blocking': False,  # ⚠️ NO bloqueante
    'message': "⚠️ Lote L-001 fue creado previamente el 2026-05-31",
    'details': "¿Debería reutilizar el lote anterior o crear uno nuevo?",
    'suggested_fix': "Opción A: Usar lote 40597.L-001 existente\nOpción B: Crear nuevo con sufijo (L-001-DUP)"
}
```

### Ventana temporal

- **Rango:** últimos 30 días
- **Razón:** Maderera típicamente no recibe mismo lote 2 veces en mes (pero puede ocurrir)
- **Acción:** WARNING, no BLOQUEANTE (permite override operativo)

---

## Validador 4: _validate_patio_capacity()

**Responsabilidad:** Validar que el patio destino tiene capacidad disponible

### Nota importante

⚠️ **SOLO APLICA SI EXISTE CAMPO DE PATIO**

Este validador está codificado para activarse **solo si**:
- El modelo tiene campo `assignment_location_id` (verificado con `hasattr`)
- El patio tiene capacidad definida (`max_capacity_m3 > 0`)
- El cálculo: `suma lotes actuales + volumen entrante ≤ max_capacity_m3`

### Lógica

1. Verifica `hasattr(self, 'assignment_location_id')`
2. Si no existe → SKIP (return silencioso)
3. Si existe:
   - Obtiene capacidad del patio (`assignment_location_id.max_capacity_m3`)
   - Si no tiene capacidad configurada → WARNING (no bloqueante)
   - Suma volumen de **todos** los lotes actuales en ese patio + volumen entrante
   - Compara contra `max_capacity_m3`

4. Si no cabe:
   - Registra **FAILED** con `is_blocking=True`
   - Muestra: utilización proyectada en porcentaje

### Resultado

```python
validation.checklist.item {
    'check_type': 'patio_capacity',
    'status': 'failed' | 'warning' | 'passed',
    'is_blocking': True,  # ← Bloqueante cuando capacidad excedida
    'message': "❌ Capacidad de patio excedida: 115.2%" 
             | "⚠️ Patio destino no tiene capacidad configurada"
             | "✅ Capacidad de patio suficiente: 78.3% proyectado",
    'details': "Volumen actual + entrante vs max_capacity_m3",
    'suggested_fix': "A) Retrasar recepción | B) Fraccionar en 2 lotes | C) Usar patio alternativo"
}
```

### Casos de uso

- **`assignment_location_id` no existe en el modelo** → SKIP silencioso
- **Patio sin `max_capacity_m3` configurado** → WARNING (no bloqueante)
- **Patio con capacidad suficiente** → PASSED
- **Patio con capacidad excedida** → FAILED (bloqueante)

---

## Validador 5: _validate_product_configuration()

**Responsabilidad:** Garantizar que productos permiten crear stock físico real (Quants) en Odoo 18

### Blindaje Odoo 18

En Odoo 18, ciertos productos **no pueden generar movimientos de stock** si:
- Tipo de producto es **Service** (debe ser Product)
- Tiene flag `is_virtual=True`
- No tiene UOM de inventario compatible

### Lógica

1. Para cada lote, valida su `product_id`:
   - Tipo = **Product** (no Service)
   - `is_virtual=False`
   - UOM permitida para stock

2. Si hay problema:
   - Registra **FAILED**
   - Establece `is_blocking=True`
   - Recomienda cambiar tipo de producto en catálogo

### Resultado

```python
validation.checklist.item {
    'check_type': 'product_configuration',
    'status': 'failed' | 'passed',
    'is_blocking': True,
    'message': "❌ Producto P-001 no puede generar stock (tipo: Service)",
    'details': "Producto: Aserrío Servicio | Tipo: Service | Inventario: Deshabilitado",
    'suggested_fix': "Cambiar tipo de producto de Service a Product en Catálogo > Productos"
}
```

### Diferencia Service vs Product

| Aspecto | Service | Product |
|---|---|---|
| Stock físico | ❌ NO | ✅ SÍ |
| Movimientos | ❌ NO | ✅ SÍ |
| Quants | ❌ NO | ✅ SÍ |
| Caso uso | Servicios (flete, aserrío) | Mercancía (madera, blanks) |

---

## Validador 6: _validate_toll_processing_genealogy()

**Responsabilidad:** Validar genealogía de lotes en canal de procesamiento por servicio

> ⚠️ **ESTADO: PLACEHOLDER — No implementado.**
> El código actual retorna PASSED sin ejecutar validación real.
> Fecha estimada de implementación: PENDIENTE.

### Aplicabilidad

⚠️ **SOLO PARA CANAL PROCESADO**

- Aplica a recepciones donde se contrata un servicio (aserrío, cepillado, etc.)
- Valida que existe padre-hijo: Lote Original → Procesado → Lote Resultado
- NO aplica a recepciones de compra bruta

### Lógica

1. Verifica si recepción es de canal **procesado** (`channel == 'processed'`)
2. Si es bruto → SKIP
3. Si es procesado:
   - Para cada lote, valida que existe campo `parent_lot_id` (lote padre)
   - Valida que padre tiene `processed_status='in_process'` o `='completed'`
   - Valida que existe documento de servicio vinculado

4. Si hay genealogía rota:
   - Registra **FAILED**
   - Establece `is_blocking=True`
   - Recomienda corregir documentación

### Resultado

```python
validation.checklist.item {
    'check_type': 'toll_processing_genealogy',
    'status': 'failed' | 'passed',
    'is_blocking': True,
    'message': "❌ Lote L-001 (procesado) no tiene lote padre definido",
    'details': "Recepción: REC-40597 (PROCESADO) | Lote: L-001 | Parent: [SIN DEFINIR]",
    'suggested_fix': "Asignar lote padre en campo 'parent_lot_id' de lote L-001"
}
```

### Modelo de datos: Genealogía

```
Lote Original (parent_lot_id: NULL)
├── parent_lot_id: NULL
├── processed_status: original
└── processing_order_id: PO-001

    ↓ (Procesado por servicio)

Lote Resultado (parent_lot_id: Lote Original)
├── parent_lot_id: [Lote Original]
├── processed_status: completed
├── processing_order_id: PO-001
└── service_type: cepillado, aserrío, etc.
```

---

## Validador 7: _validate_purchase_order_exists()

**Responsabilidad:** Validar que existe orden de compra (solo canal bruto)

> ⚠️ **ESTADO: PLACEHOLDER — No implementado.**
> El código actual retorna PASSED sin ejecutar validación real.
> Fecha estimada de implementación: PENDIENTE.

### Aplicabilidad

⚠️ **SOLO PARA CANAL BRUTO**

- Aplica a recepciones de compra normal (no servicios)
- Valida que existe `purchase_order_id` vinculada
- NO aplica a canales procesados o muestras

### Lógica

1. Verifica si recepción es de canal **bruto** (`channel == 'raw'`)
2. Si es procesado → SKIP
3. Si es bruto:
   - Valida que existe campo `purchase_order_id` poblado
   - Valida que OC está en estado válido (borrador, confirmada, recibida)
   - Valida que OC no está cancelada

4. Si no existe OC:
   - Registra **FAILED**
   - Establece `is_blocking=True` (crítico para auditoría)
   - Recomienda buscar o crear OC

### Resultado

```python
validation.checklist.item {
    'check_type': 'purchase_order_exists',
    'status': 'failed' | 'passed',
    'is_blocking': True,
    'message': "❌ Recepción REC-40597 no tiene orden de compra asignada",
    'details': "Recepción: REC-40597 (BRUTO) | OC: [SIN DEFINIR] | Proveedor: MADERA-001",
    'suggested_fix': "Opción A: Buscar OC existente del proveedor\nOpción B: Crear OC nueva para esta recepción"
}
```

### Casos especiales

| Caso | OC requerida | Notas |
|---|---|---|
| Compra normal | ✅ **SÍ** | Regla estándar |
| Servicio de procesamiento | ❌ NO | Usa purchase order de servicio (PurchaseOrderService) |
| Muestra/Regalo | ❌ NO | Requiere flag `is_sample=True` |
| Devolución | ❌ NO | Requiere flag `is_return=True` |

---

## Ejecución de Validadores

### Punto de activación

Los validadores se ejecutan en:
1. **action_confirm()** de LumberReception (confirmación)
2. **write()** sobre campos críticos (ManyOne, volumen)
3. **_compute()** automático si hay dependencias

### Orden de ejecución

```python
# Recomendado (sin dependencias entre ellos):
1. _validate_uom_consistency()            ← Prerequisito para stock
2. _validate_volumes_positive()           ← Prerequisito para cálculos
3. _validate_no_duplicate_lots()          ← Informativo
4. _validate_product_configuration()      ← Prerequisito para stock
5. _validate_patio_capacity()             ← Operacional
6. _validate_toll_processing_genealogy()  ← Solo procesado
7. _validate_purchase_order_exists()      ← Solo bruto
```

### Resultado consolidado

```python
# Antes de continuar con creación de stock:
if any(item.is_blocking and item.status == 'failed' 
       for item in self.validation_checklist_item_ids):
    raise UserError("Validaciones bloqueantes fallidas. Ver checklist.")

# Si solo warnings:
if any(item.is_blocking and item.status == 'warning'
       for item in self.validation_checklist_item_ids):
    # Mostrar warnings pero permitir override con confirmación
    self.show_validation_warnings()
```

---

## Decisiones de Diseño

### 1. Separación de validadores por responsabilidad
- Cada validador hace UNA cosa
- Facilita testing aislado
- Permite reutilización en múltiples contextos

### 2. Registro en BD vs excepciones
- ✅ **REGISTRO en validation.checklist.item** (auditado)
- ❌ NO inmediatamente exceptions (permite batch validation)
- Exceptions se lanzan en nivel superior después consolidar resultados

### 3. Bloqueante vs informativo
- **BLOQUEANTE** (`is_blocking=True`): Impide continuar (UOM, volumen, OC)
- **INFORMATIVO** (`is_blocking=False`): Requiere confirmación (capacidad, duplicados)

### 4. Contexto agnóstico
- Validadores trabajan con ANY modelo que herede `ValidationChecklistMixin`
- Funciona con recepciones, guías, orders, etc.
- Detecta automáticamente contexto (`reception_id` vs `guia_id`)

---

## Riesgos y Mitigaciones

| Riesgo | Mitigación |
|---|---|
| Validador falla silenciosamente | Registrar error en log y en checklist como WARNING |
| Performance con 1000+ lotes | Usar batch queries; considerar async para validators lentos |
| Contradicción entre validadores | Validadores son independientes; orden de ejecución en caller |
| Usuario ignora WARNING | UI debe resaltar warnings; requerir confirmación explícita |

---

## Próximos pasos

- [ ] Testear cada validador con casos reales
- [ ] Documentar en `03_TESTS.md` casos de fallo esperado
- [ ] Implementar UI para mostrar resultado de validación
- [ ] Considerar validadores adicionales: margen de ganancia, trazabilidad origen
