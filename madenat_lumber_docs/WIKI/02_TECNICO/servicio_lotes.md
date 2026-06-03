# Servicio de Lotes — LumberReceptionService

**Módulo:** `madenat_lumber_core.models.reception_service`  
**Clase:** `LumberReceptionService`  
**Versión:** 1.0.0  
**Última actualización:** 2026-06-02  
**Responsable:** Orquestación de creación de stock

---

## Propósito

El `LumberReceptionService` desacopla la complejidad de la creación de lotes (`stock.lot`) y movimientos de stock (`stock.picking`, `stock.move`) del monolito `lumber_reception.py`.

**Responsabilidad única:** Crear y validar registros de stock sin modificar los datos de recepción.

---

## Arquitectura

```
                LumberReception
                      ↓
         ┌────────────────────────┐
         │  Reception Service     │
         └────────┬───────────────┘
                  ↓
        ┌─────────────────────┐
        │ create_lots_from    │
        │ staging()           │
        └──────────┬──────────┘
                   ↓
              [stock.lot]
                   
        ┌─────────────────────┐
        │ create_stock_picking│
        │ ()                  │
        └──────────┬──────────┘
                   ↓
         ┌─────────────────────┐
         │ [stock.picking]     │
         │ [stock.move]        │
         │ [stock.move.line]   │
         └─────────────────────┘
         
        ┌─────────────────────┐
        │ cleanup_orphan_     │
        │ moves()             │
        └──────────┬──────────┘
                   ↓
         [stock.move huérfanos]
              eliminados
```

---

## Inicialización

```python
from .reception_service import LumberReceptionService

service = LumberReceptionService(env=self.env)
```

La clase requiere acceso a `env` para consultar y crear registros.

---

## Método 1: create_lots_from_staging(reception)

**Responsabilidad:** Migrar datos de staging a stock.lot real.

### Entrada
- `reception`: Instancia de `lumber.reception`
- Usa automáticamente `reception.reception_line_ids` (staging)

### Salida
- Dict con estadísticas: `{'created': int, 'updated': int, 'omitted': int}`

### Flujo

1. Itera cada línea de staging (`lumber.reception.line`)
2. Construye diccionario de valores para `stock.lot`
3. Mapea campos staging → stock.lot
4. Crea registro en `stock.lot`
5. Retorna conteo

### Mapeo de campos

| Campo Staging | Campo stock.lot | Descripción | Obligatorio |
|---|---|---|---|
| `lot_name` | `name`, `ref` | Identificador único | ✅ |
| `product_id` | `product_id` | Producto catálogo | ✅ |
| `reception_id` | `reception_id` | Recepción origen (custom) | ✅ |
| `subproduct_id` | `subproducto_id` | Subproducto (custom) | Sí |
| `pieces` | `piezas` | Cantidad piezas | Sí |
| `thickness` | `espesor_mm` | Espesor en mm | Sí |
| `width` | `ancho_mm` | Ancho en mm | Sí |
| `length` | `largo_m` | Largo en metros | Sí |
| `vol_purchase_m3` | `volume_purchase_m3` | Volumen compra m³ | ✅ |
| `vol_purchase_m3` | `volumen_m3` | Volumen stock (copia) | ✅ |
| `vol_shipment_m3` | `vol_shipment_m3` | Volumen exportación m³ | Sí |
| `thickness_visual` | `espesor_inch_frac` | Espesor visual (fraccional) | No |
| `width_visual` | `ancho_inch_frac` | Ancho visual (fraccional) | No |
| `thickness_visual` | `thickness_visual` | Copia visual | No |
| `width_visual` | `width_visual` | Copia visual | No |
| `lengthuom` == 'ft' | `length_ft` | Largo en pies (si aplica) | No |

### Ejemplo de uso

```python
service = LumberReceptionService(self.env)
stats = service.create_lots_from_staging(reception)

print(f"✅ Lotes creados: {stats['created']}")
print(f"⚠️  Lotes actualizados: {stats['updated']}")
print(f"⊘ Lotes omitidos: {stats['omitted']}")
# Output: ✅ Lotes creados: 145
```

### Notas de implementación

- **Volumen duplicado:** `vol_purchase_m3` se asigna tanto a `volume_purchase_m3` como a `volumen_m3` porque representan el stock operativo real
- **Campos visuales:** Espesor y ancho se guardan en formato visual (fraccional) para reportes comerciales
- **Largo multi-unidad:** Si la entrada fue en pies, se preserva en `length_ft`

---

## Método 2: create_stock_picking(reception)

**Responsabilidad:** Crear albarán y movimientos de stock con precisión UOM.

### Entrada
- `reception`: Instancia de `lumber.reception`
- Usa automáticamente `reception.lot_ids` (lotes creados)

### Salida
- Instancia de `stock.picking` completamente confirmado

### Flujo

1. **Buscar operación de recepción**
   - Busca `stock.picking.type` con `code='incoming'`
   - Validación: no continúa si no existe

2. **Crear cabecera del albarán**
   - Proveedor: desde recepción
   - Ubicación origen/destino: desde picking type
   - Referencia: nombre de recepción
   - Vínculo a recepción (custom)

3. **Crear movimientos y líneas**
   - Para cada lote: crea `stock.move`
   - Para cada movimiento: crea `stock.move.line`
   - UOM: metros cúbicos (hardcoded)
   - Cantidad: `lot.volume_purchase_m3` (redondeado a 3 decimales)

4. **Validar y cerrar flujo**
   - Confirma albarán
   - Asigna ubicaciones
   - Valida completitud
   - Transición a estado done

### Validaciones incorporadas

| Validación | Acción si falla |
|---|---|
| Tipo de operación 'Recepción' existe | Lanza `UserError` |
| `lot_ids` no vacío | Procede (picking sin movimientos) |
| Volumen redondeado a 3 decimales | Se redondea automáticamente |

### Ejemplo de uso

```python
service = LumberReceptionService(self.env)
picking = service.create_stock_picking(reception)

print(f"✅ Albarán creado: {picking.name}")
print(f"   Movimientos: {len(picking.move_ids)}")
print(f"   Estado: {picking.state}")
# Output: ✅ Albarán creado: IN/2026-06-02-0001
#         Movimientos: 145
#         Estado: done
```

### Estructura del Albarán

```
stock.picking
├── origin: reception.name (e.g., "REC-2026-06-02-0001")
├── partner_id: supplier
├── picking_type_id: Incoming Receipt
├── location_id: Supplier Location
├── location_dest_id: Reception Location
├── lumber_reception_id: ← Vínculo custom a recepción
│
├─ stock.move (uno por lote)
│  ├── product_id
│  ├── product_uom_qty: lot.volume_purchase_m3 (rounded)
│  ├── product_uom: m³
│  └─ stock.move.line
│     ├── lot_id: ← Asocia movimiento a lote
│     ├── quantity: lot.volume_purchase_m3
│     └── product_uom_id: m³
│
└── state: done (después de validación)
```

### Precisión UOM

- **Unidad:** metros cúbicos (`uom.product_uom_cubic_meter`)
- **Redondeo:** 3 decimales (función `float_round`)
- **Razón:** Precisión operativa en madera: volúmenes fraccionarios < 0.001 m³ son irrelevantes

---

## Método 3: cleanup_orphan_moves(origins)

**Responsabilidad:** Eliminar movimientos de stock huérfanos generados por recepciones fallidas.

### Entrada
- `origins`: List o iterable de nombres de recepción (e.g., `["REC-001", "REC-002"]`)

### Salida
- None (operación de limpieza)

### Flujo

1. **Verificar permisos**
   - Requiere grupo `stock.group_stock_manager`
   - Lanza `UserError` si usuario no autorizado

2. **Buscar movimientos huérfanos**
   - Campo: `origin` coincide con alguno de los nombres
   - Condición: `picking_id` vacío (no asociado a albarán)

3. **Eliminar en cascada**
   - Elimina `stock.move.line` asociadas
   - Pone movimientos en draft
   - Elimina `stock.move` definitivamente

### Ejemplo de uso

```python
service = LumberReceptionService(self.env)

# Limpiar movimientos de recepciones fallidas
origins = ['REC-2026-06-01-0001', 'REC-2026-06-01-0002']
service.cleanup_orphan_moves(origins)

# Si tiene permiso: silenciosamente limpia
# Si no: lanza UserError("No tienes permisos...")
```

### Guardia de seguridad

```python
# Este control previene:
# 1. Usuarios sin permiso eliminen movimientos
# 2. Borrado accidental de datos críticos
# 3. Vulnerabilidades de manipulación

if not self.env.user.has_group('stock.group_stock_manager'):
    raise UserError("No tienes permisos para eliminar movimientos de stock huérfanos.")
```

### Nota sobre orphan moves

- Los movimientos "huérfanos" son aquellos creados pero nunca asignados a un picking válido
- Ocurren cuando una recepción falla en las últimas etapas
- **No se auto-limpian:** requiere intervención manual para evitar borrado accidental

---

## Manejo de Errores

### Errores esperados

| Situación | Excepción | Acción recomendada |
|---|---|---|
| No existe `stock.picking.type` tipo 'incoming' | `UserError` | Crear operación de recepción en inventario |
| Usuario sin permisos para cleanup | `UserError` | Cambiar grupo de usuario |
| `reception_line_ids` vacío | Procede (0 lotes creados) | Verificar parseo de staging |
| `lot_ids` vacío en create_stock_picking | Procede (picking sin movimientos) | Verificar creación de lotes primero |

### Excepciones no manejadas

Si ocurren, flotan hacia el caller:
- `AttributeError`: Falta campo en recepción o lote
- `IntegrityError`: Violación de constraint DB
- Otras excepciones ORM estándar

---

## Arquitectura del Desacoplamiento

**Antes:** `lumber_reception.py` hacía todo (1500+ líneas)
```
LumberReception
├── parse_excel()
├── parse_pdf()
├── create_staging()
├── create_lots()           ← Lógica de stock
├── create_picking()        ← Lógica de stock
├── validate_financial()
└── ...
```

**Ahora:** Separación de responsabilidades
```
LumberReception
├── parse_excel()
├── parse_pdf()
├── create_staging()
└── [flujo de negocio]
       ↓
    SERVICE (desacoplado)
    ├── create_lots_from_staging()
    ├── create_stock_picking()
    └── cleanup_orphan_moves()
```

**Beneficios:**
- Mantenibilidad: cambios en stock no afectan recepción
- Testabilidad: service tiene responsabilidad única
- Reusabilidad: otros módulos pueden usar el service
- Claridad: flujo de datos es explícito

---

## Decisiones de Diseño

### 1. Service desacoplado vs Métodos en modelo
- **Elegido:** Service independiente
- **Razón:** Aislamiento de cambios de stock; facilita testing

### 2. Volumen duplicado en stock.lot
- **Elegido:** `volume_purchase_m3` + `volumen_m3`
- **Razón:** UX antigua requería `volumen_m3`; mantener compatibilidad

### 3. Limpieza de movimientos huérfanos manual
- **Elegido:** Método explícito, no automático
- **Razón:** Evitar borrado silencioso de datos; requiere intervención conscientemente

### 4. Rounding a 3 decimales
- **Elegido:** `float_round(..., precision_digits=3)`
- **Razón:** Precisión suficiente; evita ruido de operaciones floating-point

---

## Riesgos y Mitigaciones

| Riesgo | Mitigación |
|---|---|
| Creación sin lotes fallida | Gates validar antes de llamar service |
| Albarán incompleto | Validación terminal: action_confirm, action_assign, button_validate |
| Eliminación accidental de movimientos | Guardia de grupo + requiere llamada explícita |
| Performance con 1000+ lotes | Service itera sin optimización; considerar batch en futuro |
| Inconsistencia si service falla a mitad | Transacción DB maneja rollback; confiar en ORM |

---

## Integración con lumber_reception.py

### Llamadas típicas

```python
def action_process_files(self):
    # ... Gates de validación ...
    
    # Crear lotes
    service = LumberReceptionService(self.env)
    stats = service.create_lots_from_staging(self)
    _logger.info("✅ Lotes creados: %d", stats['created'])
    
    # Crear albarán
    picking = service.create_stock_picking(self)
    
    # Cambiar estado
    self.state = 'processed'
    
def action_rollback_ingestion(self):
    # Limpiar si hubo error
    service = LumberReceptionService(self.env)
    service.cleanup_orphan_moves([self.name])
```

---

## Próximos pasos

- [ ] Integrar en `action_process_files()` de `lumber_reception.py`
- [ ] Documentar casos de test en `03_TESTS.md`
- [ ] Considerar optimización para recepciones con 1000+ lotes
- [ ] Validar con datos de producción (recepciones reales)
- [ ] Documentar operación de rollback en guía de operación
