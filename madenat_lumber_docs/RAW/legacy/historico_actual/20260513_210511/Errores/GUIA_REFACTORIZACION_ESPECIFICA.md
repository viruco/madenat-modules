# 🔧 GUÍA DE REFACTORIZACIÓN ESPECÍFICA - ESTADO ACTUALIZADO

**Archivo:** `lumber_reception.py`  
**Propósito:** Soluciones concretas para problemas identificados  
**Estado Anterior (Abril 18, 2026):** 47 problemas críticos  
**Estado Actual (Mayo 1, 2026):** 6 problemas activos (87% de mejora)  
**Próximo Paso:** Eliminar 5 duplicados nuevos + Validaciones + Tests

---

## 📊 RESUMEN DE PROGRESO

### ✅ SECCIONES 1-7: COMPLETADAS (42 problemas resueltos)

| Sección | Tema | Estado | Detalle |
|---------|------|--------|---------|
| 1 | Campos duplicados (antiguos) | ✅ | lot_name, reception_id, wood_species, quality, subproduct_id |
| 2 | @api.depends duplicados | ✅ | Consolidado en línea 699-703 |
| 3 | Importaciones rotas | ✅ | Usa openpyxl nativo en línea 35 |
| 4 | Variables indefinidas | ✅ | sheet definido en línea 2827 |
| 5 | Métodos incompletos | ✅ | Todos completados (create, _onchange_*, etc.) |
| 6 | Lógica duplicada | ✅ | WidthMappingTable implementada |
| 7 | Métodos grandes | ✅ | LumberReceptionService creado |

---

## ⬜ NUEVAS SECCIONES DESCUBIERTAS (Necesarias para Fase 0.5 Final)

### SECCIÓN 8: CAMPOS DUPLICADOS NUEVOS 🆕

**Descubiertos en auditoría de Mayo 1**

#### A) `thickness_nominal` (DUPLICADO)
**Ubicación:**
- Línea 148: Primera definición
- Línea 225: Segunda definición

```python
# ❌ DUPLICADO - Eliminar línea 225
# Línea 148 (MANTENER)
thickness_nominal = fields.Float("Espesor Nom. (mm)")

# Línea 225 (ELIMINAR)
thickness_nominal = fields.Float(
    "Espesor Nom. (mm)", 
    help="Espesor teórico/comercial pactado en la OC (ej: 45mm)"
)
```

**Acción:** ✅ Eliminar línea 225  
**Tiempo:** 2 minutos

---

#### B) `export_calculation_rule` (DUPLICADO CON CONFLICTO)
**Ubicación:**
- Línea 155: Primera definición (default='metric')
- Línea 229: Segunda definición (default='f5085')

```python
# ❌ CONFLICTO DE DEFAULT
# Línea 155 (MANTENER)
export_calculation_rule = fields.Selection([
    ('metric', 'Métrico (Físico)'),
    ('f1550', 'Factor 1550 (Metros)'),
    ('f5085', 'Factor 5085 (Pies)')
], string="Regla Cálculo", default='metric')

# Línea 229 (ELIMINAR - DEFAULT CONFLICTIVO)
export_calculation_rule = fields.Selection([
    ('metric', 'Métrico (Físico)'),
    ('f1550', 'Factor 1550 (Metros)'),
    ('f5085', 'Factor 5085 (Pies)')
], string="Regla Cálculo", default='f5085')  # ← ¿Cuál gana?
```

**Acción:** ✅ Eliminar línea 229  
**Impacto:** 🔴 ALTO si defaults conflictúan (afecta cálculos)  
**Tiempo:** 2 minutos

---

#### C) `thickness_visual` (DUPLICADO)
**Ubicación:**
- Línea 162: Primera definición
- Línea 234: Segunda definición (IDÉNTICA)

```python
# ❌ DUPLICADO PURO
# Línea 162 (MANTENER)
thickness_visual = fields.Char(...)

# Línea 234 (ELIMINAR)
thickness_visual = fields.Char(...)  # EXACTAMENTE IGUAL
```

**Acción:** ✅ Eliminar línea 234  
**Tiempo:** 2 minutos

---

#### D) `width_visual` (DUPLICADO)
**Ubicación:**
- Línea 170: Primera definición
- Línea 263: Segunda definición (IDÉNTICA)

**Acción:** ✅ Eliminar línea 263  
**Tiempo:** 2 minutos

---

#### E) `product_name_clean` (DUPLICADO)
**Ubicación:**
- Línea 180: Primera definición
- Línea 302: Segunda definición (IDÉNTICA)

**Acción:** ✅ Eliminar línea 302  
**Tiempo:** 2 minutos

---

### SECCIÓN 9: REORGANIZACIÓN DE CAMPOS 🆕

**Problema:** Los campos de `LumberReceptionLine` están diseminados en dos bloques (líneas 94-180 y 220-310).

**Solución:** Reorganizar por tipo:

```python
class LumberReceptionLine(models.Model):
    _name = 'lumber.reception.line'
    
    # =================================
    # A. IDENTIDAD Y RELACIONES
    # =================================
    reception_id = fields.Many2one(...)
    lot_name = fields.Char(...)
    subproduct_id = fields.Many2one(...)
    wood_species_id = fields.Char(...)
    quality = fields.Selection(...)
    
    # =================================
    # B. DIMENSIONES REALES (Bodega)
    # =================================
    thickness = fields.Float("Espesor (mm)")
    width = fields.Float("Ancho (mm)")
    length = fields.Float("Largo (m)")
    pieces = fields.Int("Piezas")
    
    # =================================
    # C. DIMENSIONES NOMINALES (OC)
    # =================================
    thickness_nominal = fields.Float("Espesor Nom. (mm)")
    width_nominal = fields.Float("Ancho Nom. (mm)")
    length_nominal = fields.Float("Largo Nom. (m)")
    thickness_visual = fields.Char(...)
    width_visual = fields.Char(...)
    
    # =================================
    # D. VOLÚMENES CALCULADOS
    # =================================
    vol_physical_m3 = fields.Float(...)
    vol_purchase_m3 = fields.Float(...)
    vol_shipment_m3 = fields.Float(...)
    vol_mbf = fields.Float(...)
    
    # =================================
    # E. FINANCIEROS
    # =================================
    estimated_cost_usd = fields.Float(...)
    cost_clp_unit = fields.Float(...)
    currency_id = fields.Many2one(...)
    
    # =================================
    # F. AUDITORÍA Y METADATOS
    # =================================
    audit_snapshot = fields.Text(...)
    audit_hash = fields.Char(...)
    excel_product_name = fields.Char(...)
    product_name_clean = fields.Char(...)
    
    # =================================
    # G. CONFIGURACIÓN
    # =================================
    export_calculation_rule = fields.Selection(...)
```

**Tiempo:** 30 minutos

---

### SECCIÓN 10: VALIDACIONES FALTANTES 🆕

Propuestas en Fase 0.5 pero aún NO implementadas:

#### A) Validación de Rango de Volumen

```python
def _is_valid_volume(self, vol):
    """Validar que volumen esté en rango aceptable"""
    MIN_VOL = 0.1      # 100 litros mínimo
    MAX_VOL = 2000.0   # 2000 m³ máximo
    
    if not isinstance(vol, (int, float)):
        return False
    
    return MIN_VOL <= vol <= MAX_VOL
```

**Estado:** ❌ NO IMPLEMENTADO  
**Tiempo:** 30 minutos  
**Dónde usar:** En `_compute_volume_purchase()`, `_compute_export_values()`, etc.

---

#### B) Validación de Dimensiones de Lote

```python
def _validate_lot_dimensions(self, thickness, width, length):
    """Validar dimensiones de lote"""
    errors = []
    
    # Espesor: 1mm - 500mm
    if not (1 <= thickness <= 500):
        errors.append(f"Espesor inválido: {thickness}mm")
    
    # Ancho: 10mm - 500mm
    if not (10 <= width <= 500):
        errors.append(f"Ancho inválido: {width}mm")
    
    # Largo: 0.1m - 20m
    if not (0.1 <= length <= 20):
        errors.append(f"Largo inválido: {length}m")
    
    if errors:
        raise ValidationError("Dimensiones inválidas:\n" + "\n".join(errors))
```

**Estado:** ❌ NO IMPLEMENTADO  
**Tiempo:** 30 minutos  
**Dónde usar:** En `write()`, `create()`, y métodos de cálculo

---

### SECCIÓN 11: TESTS EXPANDIDOS 🆕

**Cobertura actual:** ~30%  
**Cobertura requerida:** 90%+  
**Archivo:** `tests/lumber_reception_test.py`

Tests que faltan:

```python
class TestLumberReceptionLine(TransactionCase):
    
    def test_lot_name_deduplication(self):
        """Verifica que lot_name NO esté duplicado"""
        field_count = sum(
            1 for f in self.env['lumber.reception.line']._fields
            if f == 'lot_name'
        )
        self.assertEqual(field_count, 1)
    
    def test_sanitize_lot_name(self):
        """Valida normalización de lot_name"""
        line = self.env['lumber.reception.line'].create({...})
        self.assertEqual(line.lot_name, expected_value)
    
    def test_volume_calculations(self):
        """Valida cálculos de volumen"""
        # Pruebas para vol_physical_m3, vol_purchase_m3, vol_shipment_m3
    
    def test_width_mapping_table(self):
        """Valida tabla de mapeo de anchos"""
        result = WidthMappingTable.get_value(145)
        self.assertEqual(result, "5 3/8")
    
    def test_reception_service(self):
        """Valida servicio de recepción"""
        service = LumberReceptionService(self.env)
        stats = service.create_lots_from_staging(reception)
        self.assertGreater(stats['created'], 0)
    
    def test_validation_ranges(self):
        """Valida rangos de entrada"""
        # Pruebas para _is_valid_volume()
        # Pruebas para _validate_lot_dimensions()
```

**Estado:** ⬜ PENDIENTE  
**Tiempo:** ~3 horas  
**Impacto:** Crítico para asegurar regresiones no ocurran

---

## 🎯 PLAN DE ACCIÓN FINAL PARA FASE 0.5

### Problema: `lot_name` definido DOS VECES

**Ubicación:**
- Línea 86 (primera definición)
- Línea 127 (duplicada)

**Acción:**
```python
# ❌ ELIMINAR línea 127 completamente
# El campo debe quedar como:

lot_name = fields.Char(
    string="N° Lote", 
    required=True, 
    help="Número de etiqueta o paquete"  # ← Usar esta versión
)
```

**Estado:** ✅ IMPLEMENTADO - Solo una definición encontrada en línea 139.

### Problema: `reception_id` definido DOS VECES

**Ubicación:** Línea 85 y línea 185  
**Acción:** Mantener línea 85, eliminar línea 185

**Estado:** ✅ IMPLEMENTADO - Solo una definición encontrada en línea 138.

### Problema: `wood_species_id` definido DOS VECES

**Ubicación:** Línea 88 y línea 193  
**Acción:** Mantener línea 88, eliminar línea 193

**Estado:** ✅ IMPLEMENTADO - Solo una definición encontrada en línea 141.

### Problema: `quality` definido DOS VECES

**Ubicación:** Línea 89 y línea 194  
**Acción:** Mantener línea 89, eliminar línea 194

**Estado:** ✅ IMPLEMENTADO - Solo una definición encontrada en línea 142.

### Problema: `subproduct_id` definido DOS VECES

**Ubicación:** Línea 87 y línea 243  
**Acción:** Mantener línea 87, eliminar línea 243

**Estado:** ✅ IMPLEMENTADO - Solo una definición encontrada en línea 140.

### Problema: `lot_name` definido DOS VECES

**Ubicación:**
- Línea 86 (primera definición)
- Línea 127 (duplicada)

**Acción:**
```python
# ❌ ELIMINAR línea 127 completamente
# El campo debe quedar como:

lot_name = fields.Char(
    string="N° Lote", 
    required=True, 
    help="Número de etiqueta o paquete"  # ← Usar esta versión
)
```

### Problema: `reception_id` definido DOS VECES

**Ubicación:** Línea 85 y línea 185  
**Acción:** Mantener línea 85, eliminar línea 185

### Problema: `wood_species_id` definido DOS VECES

**Ubicación:** Línea 88 y línea 193  
**Acción:** Mantener línea 88, eliminar línea 193

### Problema: `quality` definido DOS VECES

**Ubicación:** Línea 89 y línea 194  
**Acción:** Mantener línea 89, eliminar línea 194

### Problema: `subproduct_id` definido DOS VECES

**Ubicación:** Línea 87 y línea 243  
**Acción:** Mantener línea 87, eliminar línea 243

---

## SECCIÓN 2: @api.depends DUPLICADOS - SOLUCIÓN ✅ COMPLETADA

### Problema: Método `_compute_volume_purchase` con 3 decoradores idénticos

**Ubicación:** Líneas 706-710

**❌ CÓDIGO ACTUAL:**
```python
@api.depends('thickness_nominal', 'width_nominal', 'thickness', 'width', 'pieces', 'vol_shipment_m3', 'reception_id.ingestion_profile')
@api.depends('thickness_nominal', 'width_nominal', 'thickness', 'width', 'pieces', 'vol_shipment_m3', 'reception_id.ingestion_profile')
@api.depends('thickness_nominal', 'width_nominal', 'thickness', 'width', 'pieces', 'vol_shipment_m3', 'reception_id.ingestion_profile')
def _compute_volume_purchase(self):
    ...
```

**✅ CÓDIGO CORREGIDO:**
```python
@api.depends(
    'thickness_nominal', 'width_nominal', 'length_nominal', 
    'thickness', 'width', 'length', 'pieces', 
    'reception_id.ingestion_profile', 'vol_shipment_m3'
)
def _compute_volume_purchase(self):
    ...
```

**Estado:** ✅ IMPLEMENTADO - Un solo decorador consolidado encontrado en líneas 699-703.

### Problema: Método `_compute_volume_purchase` con 3 decoradores idénticos

**Ubicación:** Líneas 706-710

**❌ CÓDIGO ACTUAL:**
```python
@api.depends('thickness_nominal', 'width_nominal', 'length_nominal', 
             'thickness', 'width', 'length', 'pieces', 
             'reception_id.ingestion_profile', 'vol_shipment_m3')
@api.depends('thickness_nominal', 'width_nominal', 'thickness', 'width', 'pieces', 'vol_shipment_m3', 'reception_id.ingestion_profile')
@api.depends('thickness_nominal', 'width_nominal', 'thickness', 'width', 'pieces', 'vol_shipment_m3', 'reception_id.ingestion_profile')
def _compute_volume_purchase(self):
    ...
```

**✅ CÓDIGO CORREGIDO:**
```python
@api.depends(
    'thickness_nominal', 'width_nominal', 'length_nominal', 
    'thickness', 'width', 'length', 'pieces', 
    'reception_id.ingestion_profile', 'vol_shipment_m3'
)
def _compute_volume_purchase(self):
    ...
```

---

## SECCIÓN 3: IMPORTACIONES ROTAS - SOLUCIÓN

### Problema: `pandas` y `pdfplumber` no resueltos

**❌ ACTUAL:**
```python
import pandas as pd
import pdfplumber
```

**Opción A: Instalar las librerías (RECOMENDADO)**
```bash
pip install pandas pdfplumber
```

**Opción B: Alternativas nativas de Odoo**

```python
# Reemplazar pandas.read_excel() con:
from openpyxl import load_workbook

def _read_excel_native(self, excel_bytes):
    """Alternativa sin pandas"""
    workbook = load_workbook(filename=io.BytesIO(excel_bytes))
    sheet = workbook.active
    data = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        data.append(row)
    return data
```

---

## SECCIÓN 3: IMPORTACIONES ROTAS - SOLUCIÓN ✅ COMPLETADA

### Problema: `pandas` y `pdfplumber` no resueltos

**❌ ACTUAL:**
```python
import pandas as pd
import pdfplumber
```

**Opción A: Instalar las librerías (RECOMENDADO)**
```bash
pip install pandas pdfplumber
```

**Opción B: Alternativas nativas de Odoo**

```python
# Reemplazar pandas.read_excel() con:
from openpyxl import load_workbook
```

**Estado:** ✅ IMPLEMENTADO - Usa `from openpyxl import load_workbook` en línea 35.

## SECCIÓN 4: VARIABLES INDEFINIDAS - SOLUCIÓN ✅ COMPLETADA

### Problema: `sheet` no definido en línea 3155

**❌ CÓDIGO DEFECTUOSO:**
```python
def action_verify_data(self):
    # ... código
    for r in range(1, sheet.nrows):  # ← sheet NO EXISTE
        lote = str(sheet.cell_value(r, 0)).strip()
```

**✅ CÓDIGO CORREGIDO:**
```python
def action_verify_data(self):
    """Lee el Excel, calcula volúmenes y muestra datos para revisión"""
    self.ensure_one()
    
    if not self.excel_file:
        raise UserError("Archivo Excel requerido")
    
    excel_bytes = base64.b64decode(self.excel_file)
    workbook = load_workbook(filename=io.BytesIO(excel_bytes))
    sheet = workbook.active  # ← AHORA sheet EXISTE
    
    lines = []  # ← INICIALIZAR
    
    for r in range(2, sheet.max_row + 1):  # Comenzar en row 2 (después de header)
        try:
            lote = str(sheet.cell(r, 1).value or "").strip()
            prod = str(sheet.cell(r, 2).value or "").strip()
            qty = int(sheet.cell(r, 3).value or 0)
            vol = float(sheet.cell(r, 4).value or 0.0)
            
            if not lote:
                continue  # Saltar líneas vacías
            
            lines.append({
                'reception_id': self.id,
                'lot_name': lote,
                'product_id': self._find_or_create_product(prod).id,
                'pieces': qty,
                'vol_shipment_m3': vol,
            })
        except Exception as e:
            _logger.warning(f"Línea {r} omitida: {e}")
            continue
    
    # Guardar
    if lines:
        self.env['lumber.reception.line'].create(lines)
        self.write({'state': 'verified'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Verificado',
                'message': f'{len(lines)} líneas procesadas',
                'type': 'success'
            }
        }
    else:
        raise UserError("No se leyeron datos del Excel")
```

**Estado:** ✅ IMPLEMENTADO - `sheet` definido correctamente en línea 2827, bucle corregido.

---

## SECCIÓN 5: MÉTODOS INCOMPLETOS - SOLUCIÓN ✅ COMPLETADA

### 5.1 `_onchange_lot_name()` - Línea 150

**❌ INCOMPLETO:**
```python
@api.onchange('lot_name')
def _onchange_lot_name(self):
    # VACÍO - solo tiene docstring
```

**✅ COMPLETAR CON:**
```python
@api.onchange('lot_name')
def _onchange_lot_name(self):
    """Normaliza el lot_name cuando cambia"""
    if self.lot_name:
        self.lot_name = self._sanitize_lot_name(self.lot_name)
```

**Estado:** ✅ IMPLEMENTADO - Lógica completa en líneas 201-203.

### 5.2 `create()` - Línea 156

**❌ INCOMPLETO:**
```python
@api.model_create_multi
def create(self, vals_list):
    # VACÍO - solo docstring
```

**✅ COMPLETAR CON:**
```python
@api.model_create_multi
def create(self, vals_list):
    """Normaliza lot_name y propaga datos de producto"""
    for vals in vals_list:
        # Normalizar lot_name
        if vals.get('lot_name'):
            vals['lot_name'] = self._sanitize_lot_name(vals['lot_name'])
        
        # Copiar nombre del producto si no existe
        if not vals.get('excel_product_name') and vals.get('product_id'):
            product = self.env['product.product'].browse(vals['product_id'])
            if product.exists():
                vals['excel_product_name'] = product.name
    
    return super().create(vals_list)
```

**Estado:** ✅ IMPLEMENTADO - Lógica completa en líneas 205-216.

### 5.3 `_onchange_subproduct_id()` - Línea 312

**❌ INCOMPLETO:**
```python
@api.onchange('subproduct_id')
def _onchange_subproduct_id(self):
    """Auto-llenado de medidas nominales desde el producto"""
    # VACÍO
```

**✅ COMPLETAR CON:**
```python
@api.onchange('subproduct_id')
def _onchange_subproduct_id(self):
    """Auto-llenado de medidas nominales desde el producto"""
    if self.subproduct_id:
        # Solo inyectar si están vacíos
        if not self.thickness_nominal and self.subproduct_id.thickness_nominal:
            self.thickness_nominal = self.subproduct_id.thickness_nominal
        
        if not self.width_nominal and self.subproduct_id.width_nominal:
            self.width_nominal = self.subproduct_id.width_nominal
        
        if not self.length_nominal and self.subproduct_id.length_nominal:
            self.length_nominal = self.subproduct_id.length_nominal
```

**Estado:** ✅ IMPLEMENTADO - Lógica completa en líneas 355-375.

### 5.4 `_compute_can_process_reception()` - Línea 907

**❌ INCOMPLETO:**
```python
@api.depends('state', 'files_ready')
def _compute_can_process_reception(self):
    # VACÍO
```

**✅ COMPLETAR CON:**
```python
@api.depends('state', 'files_ready')
def _compute_can_process_reception(self):
    """Habilita botón de procesar si está en draft y archivos listos"""
    for rec in self:
        rec.can_process_reception = (rec.state == 'draft' and rec.files_ready)
```

**Estado:** ✅ IMPLEMENTADO - Lógica completa en líneas 900-902.

### 5.1 `_onchange_lot_name()` - Línea 150

**❌ INCOMPLETO:**
```python
@api.onchange('lot_name')
def _onchange_lot_name(self):
    # VACÍO - solo tiene docstring
```

**✅ COMPLETAR CON:**
```python
@api.onchange('lot_name')
def _onchange_lot_name(self):
    """Normaliza el lot_name cuando cambia"""
    if self.lot_name:
        self.lot_name = self._sanitize_lot_name(self.lot_name)
```

### 5.2 `create()` - Línea 156

**❌ INCOMPLETO:**
```python
@api.model_create_multi
def create(self, vals_list):
    # VACÍO - solo docstring
```

**✅ COMPLETAR CON:**
```python
@api.model_create_multi
def create(self, vals_list):
    """Normaliza lot_name y propaga datos de producto"""
    for vals in vals_list:
        # Normalizar lot_name
        if vals.get('lot_name'):
            vals['lot_name'] = self._sanitize_lot_name(vals['lot_name'])
        
        # Copiar nombre del producto si no existe
        if not vals.get('excel_product_name') and vals.get('product_id'):
            product = self.env['product.product'].browse(vals['product_id'])
            if product.exists():
                vals['excel_product_name'] = product.name
    
    return super().create(vals_list)
```

### 5.3 `_onchange_subproduct_id()` - Línea 312

**❌ INCOMPLETO:**
```python
@api.onchange('subproduct_id')
def _onchange_subproduct_id(self):
    """Auto-llenado de medidas nominales desde el producto"""
    # VACÍO
```

**✅ COMPLETAR CON:**
```python
@api.onchange('subproduct_id')
def _onchange_subproduct_id(self):
    """Auto-llenado de medidas nominales desde el producto"""
    if self.subproduct_id:
        # Solo inyectar si están vacíos
        if not self.thickness_nominal and self.subproduct_id.thickness_nominal:
            self.thickness_nominal = self.subproduct_id.thickness_nominal
        
        if not self.width_nominal and self.subproduct_id.width_nominal:
            self.width_nominal = self.subproduct_id.width_nominal
        
        if not self.length_nominal and self.subproduct_id.length_nominal:
            self.length_nominal = self.subproduct_id.length_nominal
```

### 5.4 `_compute_can_process_reception()` - Línea 907

**❌ INCOMPLETO:**
```python
@api.depends('state', 'files_ready')
def _compute_can_process_reception(self):
    # VACÍO
```

**✅ COMPLETAR CON:**
```python
@api.depends('state', 'files_ready')
def _compute_can_process_reception(self):
    """Habilita botón de procesar si está en draft y archivos listos"""
    for rec in self:
        rec.can_process_reception = (rec.state == 'draft' and rec.files_ready)
```

---

## SECCIÓN 6: LÓGICA DUPLICADA - CONSOLIDACIÓN ✅ COMPLETADA

### Problema: `_get_trader_width_text()` vs `_get_excel_mapping()`

**Propuesta:** Crear tabla centralizada

**✅ SOLUCIÓN:**
```python
# Nueva clase auxiliar
class WidthMappingTable:
    """Tabla única de mapeo de anchos"""
    
    # Formato: mm -> (decimal, texto)
    MAPPING = {
        75:   (2.625, "2 5/8"),
        85:   (2.875, "2 7/8"),
        90:   (3.125, "3 1/8"),
        95:   (3.375, "3 3/8"),
        100:  (3.625, "3 5/8"),
        105:  (3.875, "3 7/8"),
        110:  (3.875, "3 7/8"),
        115:  (4.375, "4 3/8"),
        120:  (4.375, "4 3/8"),
        125:  (4.625, "4 5/8"),
        130:  (4.875, "4 7/8"),
        140:  (4.875, "4 7/8"),
        145:  (5.375, "5 3/8"),
        150:  (5.625, "5 5/8"),
        155:  (5.875, "5 7/8"),
    }
    
    @classmethod
    def get_value(cls, mm, format='text', tolerance=2.5):
        """
        Obtiene valor de ancho
        
        Args:
            mm: medida en milímetros
            format: 'text' (5 3/8) o 'decimal' (5.375)
            tolerance: tolerancia de búsqueda ±mm
        
        Returns:
            Valor mapeado o None
        """
        # Búsqueda exacta primero
        if mm in cls.MAPPING:
            value = cls.MAPPING[mm]
            return value[1] if format == 'text' else value[0]
        
        # Búsqueda por vecino más cercano
        matches = [
            (m, v) for m, v in cls.MAPPING.items()
            if abs(m - mm) <= tolerance
        ]
        
        if not matches:
            return None
        
        # Tomar el más cercano
        closest_mm, closest_val = min(matches, key=lambda x: abs(x[0] - mm))
        return closest_val[1] if format == 'text' else closest_val[0]

# Ahora los métodos quedan:
def _get_trader_width_text(self, value_mm):
    """Obtiene texto S2S del ancho"""
    if not value_mm:
        return ""
    return WidthMappingTable.get_value(value_mm, format='text') or self._fallback_width_text(value_mm)

def _get_excel_mapping(self, mm_value):
    """Obtiene decimal S2S del ancho"""
    if not mm_value:
        return 0.0
    return WidthMappingTable.get_value(mm_value, format='decimal') or 0.0
```

---

## SECCIÓN 7: REFACTORIZACIÓN DE `_create_lots_from_packing` ✅ COMPLETADA

### Problema: Método demasiado grande (170+ líneas)

**Propuesta:** Extraer a servicio separado

**✅ CREAR NUEVA CLASE:**
```python
# En archivo: madenat_lumber_core/models/reception_service.py

class LumberReceptionService:
    """Servicio de negocio para procesamiento de recepciones"""
    
    def __init__(self, env):
        self.env = env
        self.logger = logging.getLogger(__name__)
    
    def create_lots_from_packing_list(self, reception, packing_data):
        """
        Crea lotes desde datos del packing list
        
        Args:
            reception: lumber.reception record
            packing_data: dict con 'lines' y metadatos
        
        Returns:
            Diccionario con estadísticas de creación
        """
        lines = packing_data.get('lines', [])
        stats = {
            'created': 0,
            'updated': 0,
            'omitted': 0,
            'errors': []
        }
        
        for idx, line_data in enumerate(lines, 1):
            try:
                lot = self._process_single_lot(reception, line_data)
                if lot.id:
                    stats['created'] += 1
            except Exception as e:
                stats['omitted'] += 1
                stats['errors'].append(f"Línea {idx}: {e}")
        
        return stats
    
    def _process_single_lot(self, reception, line_data):
        """Procesa UN lote individual"""
        # Lógica desacoplada...
        pass

# Usar en lumber_reception.py:
def _create_lots_from_packing(self, pl_data):
    service = LumberReceptionService(self.env)
    stats = service.create_lots_from_packing_list(self, pl_data)
    
    # Logs y auditoría
    self._add_log(f"✅ Lotes creados: {stats['created']}")
    if stats['errors']:
        self._add_log(f"⚠️ Omisiones: {len(stats['errors'])}")
```

---

## SECCIÓN 8: VALIDACIONES FALTANTES ⬜ PENDIENTE

### Agregar validación de rango de volumen

```python
def _is_valid_volume(self, vol):
    """Validar que volumen esté en rango aceptable"""
    MIN_VOL = 0.1      # 100 litros mínimo
    MAX_VOL = 2000.0   # 2000 m³ máximo
    
    if not isinstance(vol, (int, float)):
        return False
    
    return MIN_VOL <= vol <= MAX_VOL

def _validate_lot_dimensions(self, thickness, width, length):
    """Validar dimensiones de lote"""
    errors = []
    
    # Espesor: 1mm - 500mm
    if not (1 <= thickness <= 500):
        errors.append(f"Espesor inválido: {thickness}mm")
    
    # Ancho: 10mm - 500mm
    if not (10 <= width <= 500):
        errors.append(f"Ancho inválido: {width}mm")
    
    # Largo: 0.1m - 20m
    if not (0.1 <= length <= 20):
        errors.append(f"Largo inválido: {length}m")
    
    if errors:
        raise ValidationError("Dimensiones inválidas:\n" + "\n".join(errors))
```

**Estado:** ⬜ PENDIENTE - Métodos no encontrados en el código actual.

### Agregar validación de rango de volumen

```python
def _is_valid_volume(self, vol):
    """Validar que volumen esté en rango aceptable"""
    MIN_VOL = 0.1      # 100 litros mínimo
    MAX_VOL = 2000.0   # 2000 m³ máximo
    
    if not isinstance(vol, (int, float)):
        return False
    
    return MIN_VOL <= vol <= MAX_VOL

def _validate_lot_dimensions(self, thickness, width, length):
    """Validar dimensiones de lote"""
    errors = []
    
    # Espesor: 1mm - 500mm
    if not (1 <= thickness <= 500):
        errors.append(f"Espesor inválido: {thickness}mm")
    
    # Ancho: 10mm - 500mm
    if not (10 <= width <= 500):
        errors.append(f"Ancho inválido: {width}mm")
    
    # Largo: 0.1m - 20m
    if not (0.1 <= length <= 20):
        errors.append(f"Largo inválido: {length}m")
    
    if errors:
        raise ValidationError("Dimensiones inválidas:\n" + "\n".join(errors))
```

---

## SECCIÓN 9: TESTING ⬜ PENDIENTE

### Crear tests unitarios para validar cambios

```python
# En: madenat_lumber_core/tests/test_lumber_reception.py

class TestLumberReceptionLine(TransactionCase):
    
    def setUp(self):
        super().setUp()
        self.reception = self.env['lumber.reception'].create({
            'name': 'TEST-001',
            'ingestion_profile': 'metric'
        })
    
    def test_lot_name_deduplication(self):
        """Verifica que lot_name no esté duplicado"""
        field_count = sum(
            1 for f in self.env['lumber.reception.line']._fields
            if f == 'lot_name'
        )
        self.assertEqual(field_count, 1, "lot_name duplicado en modelo")
    
    def test_sanitize_lot_name(self):
        """Valida normalización de lot_name"""
        line = self.env['lumber.reception.line'].create({
            'reception_id': self.reception.id,
            'lot_name': '123.0'  # Excel puede enviar con .0
        })
        self.assertEqual(line.lot_name, '123')
```

**Estado:** ⬜ PENDIENTE - Existen tests básicos en `tests/lumber_reception_test.py`, pero no cubren todas las validaciones propuestas.

### Crear tests unitarios para validar cambios

```python
# En: madenat_lumber_core/tests/test_lumber_reception.py

class TestLumberReceptionLine(TransactionCase):
    
    def setUp(self):
        super().setUp()
        self.reception = self.env['lumber.reception'].create({
            'name': 'TEST-001',
            'ingestion_profile': 'metric'
        })
    
    def test_lot_name_deduplication(self):
        """Verifica que lot_name no esté duplicado"""
        field_count = sum(
            1 for f in self.env['lumber.reception.line']._fields
            if f == 'lot_name'
        )
        self.assertEqual(field_count, 1, "lot_name duplicado en modelo")
    
    def test_sanitize_lot_name(self):
        """Valida normalización de lot_name"""
        line = self.env['lumber.reception.line'].create({
            'reception_id': self.reception.id,
            'lot_name': '123.0'  # Excel puede enviar con .0
        })
        self.assertEqual(line.lot_name, '0000000000123')  # 13 dígitos
    
    def test_volume_calculation(self):
        """Verifica cálculo de volumen"""
        line = self.env['lumber.reception.line'].create({
            'reception_id': self.reception.id,
            'lot_name': 'LOT-001',
            'thickness': 45,  # mm
            'width': 100,     # mm
            'length': 5,      # m
            'pieces': 10
        })
        expected = (45 * 100 * 5 * 10) / 1_000_000  # 0.225 m³
        self.assertAlmostEqual(line.vol_physical_m3, expected, places=3)
```

---

## CHECKLIST DE IMPLEMENTACIÓN

- [ ] **Semana 1:**
  - [ ] Eliminar campos duplicados (lot_name, reception_id, etc.)
  - [ ] Consolidar @api.depends
  - [ ] Instalar/resolver importaciones
  - [ ] Crear tests para validar cambios

- [ ] **Semana 2:**
  - [ ] Implementar métodos vacíos
  - [ ] Añadir validaciones
  - [ ] Crear WidthMappingTable
  - [ ] Ejecutar test suite completa

- [ ] **Semana 3:**
  - [ ] Extraer LumberReceptionService
  - [ ] Refactorizar _create_lots_from_packing
  - [ ] Validación en producción (datos reales)

- [ ] **Semana 4:**
  - [ ] Performance testing
  - [ ] Optimizar N+1 queries
  - [ ] Documentación final

---

## COMANDOS ÚTILES

```bash
# Validar sintaxis
python -m py_compile lumber_reception.py

# Lint con flake8
flake8 lumber_reception.py --max-line-length=120

# Lint con pylint
pylint lumber_reception.py --disable=all --enable=E,F

# Generar reporte de complejidad
radon mi lumber_reception.py -s

# Ejecutar tests
python manage.py test madenat_lumber_core.tests.test_lumber_reception
```

---

*Este documento es complemento al INFORME_AUDITORIA_CODIGO.md*

---

## 🆕 ACTUALIZACIÓN 2026-05-01: NUEVOS PROBLEMAS DETECTADOS

Después de la auditoría completa del código, se descubrieron **5 campos duplicados NUEVOS** que no estaban en la auditoría original del Abril 18.

---

### SECCIÓN 8: CAMPOS DUPLICADOS NUEVOS (Mayo 1)

#### Problema 1: `thickness_nominal` duplicado
- **Línea 148:** Primera definición (MANTENER)
- **Línea 225:** Segunda definición (ELIMINAR)
- **Impacto:** ⚠️ Medio
- **Acción:** Eliminar línea 225
- **Tiempo:** 2 minutos

#### Problema 2: `export_calculation_rule` duplicado CON CONFLICTO
- **Línea 155:** First definition with `default='metric'` (KEEP)
- **Línea 229:** Second definition with `default='f5085'` (DELETE) ⚠️
- **Impacto:** 🔴 ALTO - Los defaults conflictúan
- **Acción:** Eliminar línea 229
- **Tiempo:** 2 minutos

#### Problema 3: `thickness_visual` duplicado
- **Línea 162:** Primera definición (MANTENER)
- **Línea 234:** Segunda definición idéntica (ELIMINAR)
- **Impacto:** ⚠️ Medio
- **Acción:** Eliminar línea 234
- **Tiempo:** 2 minutos

#### Problema 4: `width_visual` duplicado
- **Línea 170:** Primera definición (MANTENER)
- **Línea 263:** Segunda definición idéntica (ELIMINAR)
- **Impacto:** ⚠️ Medio
- **Acción:** Eliminar línea 263
- **Tiempo:** 2 minutos

#### Problema 5: `product_name_clean` duplicado
- **Línea 180:** Primera definición (MANTENER)
- **Línea 302:** Segunda definición idéntica (ELIMINAR)
- **Impacto:** ⚠️ Medio
- **Acción:** Eliminar línea 302
- **Tiempo:** 2 minutos

---

### SECCIÓN 9: REORGANIZACIÓN DE CAMPOS

**Problema:** Los campos están en 2 bloques separados (líneas 94-180 y 220-310).

**Solución propuesta:** Agrupar por tipo lógico:
1. Identidad y Relaciones
2. Dimensiones Reales (Bodega)
3. Dimensiones Nominales (OC/Comercial)
4. Volúmenes Calculados
5. Datos Financieros
6. Auditoría y Metadatos
7. Configuración

**Tiempo:** 30 minutos

---

### SECCIÓN 10: VALIDACIONES FALTANTES

#### A) `_is_valid_volume()` - NO IMPLEMENTADO
```python
def _is_valid_volume(self, vol):
    MIN_VOL = 0.1
    MAX_VOL = 2000.0
    return isinstance(vol, (int, float)) and MIN_VOL <= vol <= MAX_VOL
```
**Tiempo:** 30 minutos

#### B) `_validate_lot_dimensions()` - NO IMPLEMENTADO
```python
def _validate_lot_dimensions(self, thickness, width, length):
    errors = []
    if not (1 <= thickness <= 500): errors.append(f"Espesor inválido")
    if not (10 <= width <= 500): errors.append(f"Ancho inválido")
    if not (0.1 <= length <= 20): errors.append(f"Largo inválido")
    if errors: raise ValidationError("\n".join(errors))
```
**Tiempo:** 30 minutos

---

### SECCIÓN 11: TESTS EXPANDIDOS

**Cobertura Actual:** 30%  
**Cobertura Requerida:** 90%+

Tests que faltan:
- ❌ test_lot_name_deduplication
- ❌ test_sanitize_lot_name
- ❌ test_volume_calculations
- ❌ test_width_mapping_table
- ❌ test_reception_service
- ❌ test_validation_ranges

**Tiempo:** ~3 horas

---

## 🎯 PLAN FINAL PARA COMPLETAR FASE 0.5

### HOY (2-3 HORAS)
1. Eliminar 5 duplicados (10 min)
2. Reorganizar campos (30 min)
3. Verificar compilación (15 min)

### ESTA SEMANA (4-6 HORAS)
1. Implementar validaciones (1 hora)
2. Expandir tests (3 horas)
3. Verificación final (1-2 horas)

### RESULTADO
✅ Fase 0.5 = 100% COMPLETADA  
✅ Código PRODUCTION-READY  
✅ Listo para Fase 3
