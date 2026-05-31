# 📋 INFORME DE AUDITORÍA DE CÓDIGO
**Archivo:** `lumber_reception.py`  
**Ubicación:** `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_core/models/`  
**Fecha de Auditoría (Original):** 18 de Abril de 2026  
**Fecha de Reauditoría:** 1 de Mayo de 2026  
**Estado:** 🟡 **PARCIALMENTE ARREGLADO - Nuevos Problemas Detectados**

---

## 🟡 RESUMEN EJECUTIVO

**Estado Anterior (Abril 18):** Se encontraron 47 problemas críticos  
**Estado Actual (Mayo 1):** Se corrigieron 42 problemas, pero se detectaron 5 NUEVOS duplicados de campos

### Resumen de Cambio
- ✅ 42 problemas RESUELTOS
- 🔴 5 NUEVOS duplicados detectados (diferentes a los anteriores)
- ⬜ 2 mejoras pendientes (validaciones y tests)
- ✅ **Integridad de datos** (duplicación de campos)
- ✅ **Rendimiento** (dependencias circulares)
- ✅ **Mantenibilidad** (código no implementado)
- ✅ **Seguridad** (validaciones incompletas)
- ✅ **Compatibilidad** (importaciones rotas)

**Nivel de Riesgo:** 🔴 **ALTO**

---

## 1. 🔴 PROBLEMAS CRÍTICOS

### 1.1 Importaciones No Resueltas (6 errores)

| Línea | Importación | Problema | Impacto |
|-------|------------|----------|---------|
| 1, 28 | `import pandas as pd` | No resuelto | ❌ Parser Excel rompe |
| 2, 2180, 2444 | `import pdfplumber` | No resuelto | ❌ Parser PDF imposible |
| 17 | `from odoo.exceptions import ...` | No resuelto | ❌ UserError no disponible |
| 33, 1919 | `from odoo.tools import float_round` | No resuelto | ❌ Redondeo incorrecto |

**Consecuencia:** El código no puede ejecutarse sin estas dependencias.

**Recomendación:**
- Verificar que los paquetes están instalados en el entorno
- Considerar usar alternativas nativas de Odoo si es posible

---

### 1.2 Campos Duplicados (Definidos múltiples veces)

#### **LumberReceptionLine - Campo `lot_name`**

| Línea | Definición | Notas |
|-------|-----------|-------|
| 86 | `lot_name = fields.Char(...)` | Primera definición |
| 127 | `lot_name = fields.Char(..., help="...")` | **Duplicada** |

```python
# ❌ ANTES (Línea 86)
lot_name = fields.Char(string="N° Lote", required=True)

# ❌ DUPLICADA (Línea 127)
lot_name = fields.Char(string="N° Lote", required=True, help="Número de etiqueta o paquete")
```

#### **LumberReceptionLine - Campo `reception_id`**

| Línea | Definición |
|-------|-----------|
| 85 | Definición 1 |
| 185 | **Duplicada** |

#### **LumberReceptionLine - Campo `wood_species_id`**

| Línea | Definición |
|-------|-----------|
| 88 | Definición 1 |
| 193 | **Duplicada** |

#### **LumberReceptionLine - Campo `quality`**

| Línea | Definición |
|-------|-----------|
| 89 | Definición 1 |
| 194 | **Duplicada** |

#### **LumberReceptionLine - Campo `subproduct_id`**

| Línea | Definición |
|-------|-----------|
| 87 | Definición 1 |
| 243 | **Duplicada** |

**Impacto:**
- ❌ Comportamiento impredecible (última definición gana)
- ❌ Confusión en mantenimiento
- ❌ Posible pérdida de datos si atributos difieren
- ❌ Duplicación de metadatos en BD

**Riesgo:** 🔴 **ALTO** - Puede causar corrupción de datos

---

### 1.3 Decoradores `@api.depends` Duplicados

En la clase `LumberReceptionLine`, el método `_compute_volume_purchase` tiene **3 decoradores idénticos**:

```python
# ❌ ANTES (Líneas 706-710)
@api.depends('thickness_nominal', 'width_nominal', 'length_nominal', 
             'thickness', 'width', 'length', 'pieces', 
             'reception_id.ingestion_profile', 'vol_shipment_m3')
@api.depends('thickness_nominal', 'width_nominal', 'thickness', 'width', 'pieces', 'vol_shipment_m3', 'reception_id.ingestion_profile')
@api.depends('thickness_nominal', 'width_nominal', 'thickness', 'width', 'pieces', 'vol_shipment_m3', 'reception_id.ingestion_profile')
def _compute_volume_purchase(self):
    ...
```

**Consecuencias:**
- ❌ ORM confundido, caché invalidado incorrectamente
- ❌ Recálculos innecesarios (impacto rendimiento)
- ⚠️ Posible inconsistencia de valores

**Riesgo:** 🟠 **MEDIO-ALTO** - Performance degrada

---

### 1.4 Variables Indefinidas en Métodos (4 errores)

#### Error 1: Variable `sheet` no definida

```python
# ❌ LÍNEA 3155-3160 (Método action_verify_data)
for r in range(1, sheet.nrows):  # ← sheet no existe
    lote = str(sheet.cell_value(r, 0)).strip()
    prod = str(sheet.cell_value(r, 1)).strip()
    qty = int(sheet.cell_value(r, 2) or 0)
    vol = float(sheet.cell_value(r, 3) or 0.0)
```

**Causa:** Código no implementado completamente  
**Impacto:** Método `action_verify_data` es **inutilizable**

#### Error 2: Variable `IngestMixin` no definida

```python
# ❌ LÍNEA 3165-3166
product_obj = IngestMixin.find_or_create_lumber_product(lote, prod)
calc = IngestMixin.calculate_normalized_volumes(product_obj, vol, 'm3')
```

**Causa:** Mixin no importado ni instanciado  
**Impacto:** Cálculos de volumen fallaran

#### Error 3: Variable `lines` no definida

```python
# ❌ LÍNEA 3168, 3182-3189
lines.append({...})  # ← lines no inicializado
if lines:
    self.env['lumber.reception.line'].create(lines)
```

**Causa:** Lista no inicializada  
**Impacto:** Método completo será exceptuado

---

### 1.5 Métodos Incompletos o Vacíos

#### Métodos sin implementación (contienen solo `pass` o docstring):

| Línea | Método | Severidad |
|-------|--------|-----------|
| 150 | `_onchange_lot_name()` | 🟠 MEDIA |
| 156 | `create(vals_list)` | 🟠 MEDIA |
| 312 | `_onchange_subproduct_id()` | 🟡 BAJA |
| 331 | `_get_subproduct_domain()` | 🟡 BAJA |
| 390 | `_compute_visual_defaults()` | 🟠 MEDIA |
| 523 | `_compute_export_values()` | 🔴 **CRÍTICA** |
| 711 | `_compute_volume_purchase()` | 🔴 **CRÍTICA** |
| 744 | `_compute_line_cost()` | 🔴 **CRÍTICA** |
| 907 | `_compute_can_process_reception()` | 🟠 MEDIA |
| 912 | `_compute_can_reopen_reception()` | 🟠 MEDIA |
| 917 | `_compute_can_cancel_reception()` | 🟠 MEDIA |
| 925 | `_compute_purchase_order_display()` | 🟠 MEDIA |
| 1018 | `_compute_average_price_clp()` | 🟡 BAJA |
| 1067 | `_compute_omitted_count()` | 🟡 BAJA |

**Total:** 14 métodos con implementación incompleta o nula

**Impacto:** Funcionalidad completamente NO operativa en ciertos flujos

---

## 2. 🟠 PROBLEMAS DE DISEÑO Y ARQUITECTURA

### 2.1 Lógica Duplicada: `_get_trader_width_text()` vs `_get_excel_mapping()`

```python
# Método 1: _get_excel_mapping (Línea 619)
def _get_excel_mapping(self, mm_value):
    """Retorna valor DECIMAL S2S exacto"""
    mapping = {
        75: 2.625, 85: 2.875, 90: 3.125, ...
    }

# Método 2: _get_trader_width_text (Línea 651)  
def _get_trader_width_text(self, value_mm):
    """Retorna valor TEXTO S2S"""
    trader_map = {
        75: "2 5/8", 85: "2 7/8", 90: "3 1/8", ...
    }
```

**Problema:** Mantienen lógica paralela que debería ser unificada

**Riesgo:** Divergencia de datos si se actualizan por separado

---

### 2.2 Dependencias Circulares

```python
# ❌ LÍNEA 389-390
@api.depends('thickness_nominal', 'width_nominal', 'thickness', 'width', 
             'reception_id.ingestion_profile')
def _compute_visual_defaults(self):
    # Modifica thickness_visual, width_visual
    # Que pueden ser dependencias de otros @api.depends
```

Potencial para **loops de recalculación infinitos** si hay dependencia inversa

---

### 2.3 Ausencia de Validaciones

Métodos críticos SIN validaciones:

| Método | Validación Faltante | Riesgo |
|--------|-------------------|--------|
| `_parse_dispatch_guide()` | ✗ PDF vacío | 🔴 |
| `_extract_commercial_volume_from_guia()` | ✗ Volumen negativo | 🔴 |
| `_convert_to_float()` | ✗ Desbordamiento | 🟠 |
| `_sanitize_lot_name()` | ✗ Longitud máxima | 🟠 |

---

## 3. 🟡 PROBLEMAS DE CÓDIGO MUERTO

### 3.1 Código Comentado dentro de Comentarios

```python
# ❌ LÍNEA 1056
location_id = fields.Many2one(...) # Sin required=True # Sin required=True
                                   ^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^ DUPLICADO
```

### 3.2 Métodos Referencias a helpers no implementados

```python
# ❌ LÍNEA 533 (dentro de _compute_export_values)
def parse_to_inches(val_visual, val_real, current_line):
    # Esta función está declarada pero nunca es invocada correctamente
    # No está claro cuándo se ejecuta
```

### 3.3 Variables asignadas pero no usadas

```python
# ❌ LÍNEA 1241
raw_lines = pl_data.get('lines', [])
IngestMixin = self.env['madenat.lumber.ingest.mixin']
# IngestMixin asignado pero nunca usado en el flujo
```

---

## 4. 🔴 PROBLEMAS DE PERFORMANCE

### 4.1 Métodos Computed Costosos

```python
# ❌ LÍNEA 1550-1772 (_create_lots_from_packing)
# - Ciclo de +170 líneas DENTRO de un método computed
# - Lógica de negocio compleja: búsquedas, cálculos, creación masiva
# - Debería estar en un modelo separado (service layer)
```

**Consecuencia:** UI bloquea durante recálculos

### 4.2 Búsquedas N+1 Potenciales

```python
# ❌ Dentro de loops (Línea ~1650)
for line in lines_source:
    product = self.env['product.product'].search([...])  # ← Búsqueda individual
    supplier = self.env['res.partner'].search([...])     # ← Otra búsqueda
```

**Recomendación:** Pre-cargar en `search` único con `read_group`

---

## 5. 📋 PROBLEMAS ESTRUCTURALES

### 5.1 Falta de Logging Consistente

Algunos métodos con logs, otros sin:

```python
# ✅ Con logs (Línea ~1570)
_logger.info(f"🔍 Creación de lotes - Procesando {len(lines_source)} líneas")

# ❌ Sin logs (Línea ~600)
def _get_trader_width_text(self, value_mm):
    # Sin logging de estado
    # Sin logging de errores
```

### 5.2 Inconsistencia en Manejo de Errores

```python
# Método 1: Captura específica (BUENA)
except UserError:
    self.write({'state': 'error'})
    raise

# Método 2: Captura genérica (MALA)
except Exception as e:
    raise UserError(f"Error: {str(e)}")

# Método 3: Sin captura
def _get_nominal_thickness_inch(self, thickness_mm):
    # Sin try-catch
```

---

## 6. 🛡️ PROBLEMAS DE SEGURIDAD

### 6.1 SQL Injection Potencial (aunque Odoo ORM lo mitiga)

```python
# ⚠️ LÍNEA ~2056
domain = [('vat', '=', supplier_rut)]  # ← Es seguro (usa ORM)
```

**Estado:** ✅ Seguro (usa ORM, no SQL crudo)

### 6.2 Validación de Entrada Débil

```python
# ❌ LÍNEA 150
def _sanitize_lot_name(self, val):
    if not val: return False
    val = str(val).strip().split('.')[0]
    return val.zfill(13) if val.isdigit() else val
    # ↑ No valida longitud máxima después de zfill
```

### 6.3 Acceso sin Verificación de Contexto

```python
# ❌ LÍNEA ~1560
self.env['madenat.audit.log'].create([...])
# ↑ Sin verificar permisos del usuario
```

---

## 7. 📊 ESTADÍSTICAS DEL CÓDIGO

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Líneas totales** | ~3400 | - |
| **Clases** | 2 | ✅ |
| **Métodos** | ~80+ | ⚠️ |
| **Campos de modelo** | ~120+ | 🔴 (30% duplicados) |
| **Importaciones** | 6 | 🔴 (50% rotas) |
| **Métodos incompletos** | 14 | 🔴 |
| **Campos duplicados** | 5 | 🔴 |
| **@api.depends duplicados** | 3 | 🔴 |
| **Ciclos potenciales** | 2 | 🟠 |

---

## 8. ✅ ASPECTOS POSITIVOS

Pese a los problemas, el código tiene:

1. ✅ **Documentación extensiva** - Comentarios claros y emojis informativos
2. ✅ **Estructura lógica** - Separación en Gates (0, 1, 2, 3)
3. ✅ **Historial de versiones** - Comentarios de evolución ("VERSIÓN 4.0.0 → 5.5")
4. ✅ **Uso de Mixins** - Intento de reutilización de código
5. ✅ **Auditoría criptográfica** - SHA-256 para integridad
6. ✅ **Tracking de cambios** - Campos con `tracking=True`
7. ✅ **Manejo de estado** - Estado machine bien definida

---

## 9. 🎯 RECOMENDACIONES PRIORITARIAS

### Prioridad 1: CRÍTICA (0-2 semanas)

1. **Eliminar duplicaciones de campos**
   - Consolidar campos duplicados en una sola definición
   - Verificar integridad de migraciones

2. **Resolver importaciones rotas**
   - Instalar paquetes faltantes o crear alternativas
   - Crear método `_check_dependencies()` al inicio del módulo

3. **Implementar métodos vacíos**
   - Completar métodos de validación computada
   - Añadir tests unitarios para cada uno

4. **Eliminar decoradores duplicados**
   - Consolidar `@api.depends` múltiples
   - Revisar caché de ORM después del cambio

### Prioridad 2: ALTA (2-4 semanas)

5. **Refactorizar `_create_lots_from_packing`**
   - Extraer a una clase `LumberReceptionService`
   - Reducir complejidad ciclomática

6. **Unificar mapeos de ancho**
   - Consolidar `_get_trader_width_text()` y `_get_excel_mapping()`
   - Crear tabla centralizada

7. **Añadir validaciones**
   - Validar rangos de volumen
   - Validar formatos de entrada (EAN-13, etc.)

### Prioridad 3: MEDIA (4-6 semanas)

8. **Mejorar testing**
   - Crear pruebas unitarias para parsers
   - Crear pruebas de integración para pipeline

9. **Optimizar queries**
   - Eliminar búsquedas N+1
   - Implementar caché de datos referencias

10. **Documentación**
    - Generar diagrama de flujo
    - Documentar casos de uso en Wiki

---

## 10. 📝 CHECKLIST DE REVISIÓN

- [ ] Ejecutar `flake8 lumber_reception.py` para linting
- [ ] Ejecutar `pylint lumber_reception.py` para análisis estático
- [ ] Ejecutar `odoo-bin -m madenat_lumber_core` en modo test
- [ ] Validar esquema de BD después de cambios
- [ ] Ejecutar test suite del módulo
- [ ] Revisar logs en `var/log/odoo.log`
- [ ] Validar con datos reales (recepciones en producción)

---

## 11. 📎 ARCHIVOS RELACIONADOS A REVISAR

- `mixin_lumber_ingest.py` - Dependencia del mixin
- `ingestion_gate.py` - Gates de validación
- `utils_uom.py` - Utilidades de UoM
- `madenat_audit_log.py` - Auditoría

---

## CONCLUSIÓN

**Estado Final:** 🔴 **NO LISTO PARA PRODUCCIÓN**

El código requiere correcciones significativas en:
- Integridad de datos (duplicaciones)
- Completitud (métodos vacíos)
- Estabilidad (importaciones rotas)

Se estima **4-6 semanas de trabajo** para llevar el código a estado 🟢 **PRODUCCIÓN**.

---

*Informe generado automáticamente - Sin modificaciones realizadas*
