# 🚀 GUÍA DE CONTINUIDAD TÉCNICA - Fase 0.5 Completada

**Fecha:** 2 de mayo de 2026  
**Estado:** 🟢 Listo para producción  
**Objetivo:** Permitir que cualquier desarrollador continúe desde donde se dejó  

---

## 📌 TL;DR (Lee esto primero)

### Estado Actual
- ✅ Código compila sin errores
- ✅ Tests pasan en Docker
- ✅ Validaciones implementadas
- ✅ Duplicados eliminados
- ✅ Manifest ordenado correctamente

### Si necesitas continuar...
1. Lee `/docs/00_ARQUITECTURA.md` (decisiones base)
2. Lee `/docs/Errores/AUDITORIA_2026_05_02.md` (estado actual detallado)
3. Lee ESTE documento (cómo trabajar desde aquí)

---

## 🏗️ ARQUITECTURA ACTUAL

### Capas del Módulo

```
ENTRADA (Gates) → STAGING (Líneas) → VALIDACIÓN → PERSISTENCIA (Stock) → SALIDA (Exportación)
```

### Modelos Principales

| Modelo | Responsabilidad | Ubicación |
|--------|-----------------|-----------|
| `lumber.reception` | Cabecera de recepción, maestro | `lumber_reception.py:1000-2000` |
| `lumber.reception.line` | Líneas de staging, validación | `lumber_reception.py:100-900` |
| `stock.lot` | Lotes reales (Odoo stock) | Creados por `LumberReceptionService` |
| `WidthMappingTable` | Tabla de mapeo de anchos | `lumber_reception.py:45-90` |

---

## 🔧 CÓMO TRABAJAR CON EL CÓDIGO

### Estructura de Campos en `LumberReceptionLine`

Los campos están organizados en **7 secciones lógicas**:

```python
class LumberReceptionLine(models.Model):
    # SECCIÓN 1: IDENTIDAD (lot_name, product, subproduct)
    reception_id = ...  # Relación a lumber.reception
    lot_name = ...      # Identificador único (EAN-13 normalizado)
    product_id = ...    # Referencia a producto
    subproduct_id = ... # Subproducto/Grado
    
    # SECCIÓN 2: DIMENSIONES NOMINALES (Lo que dice la OC)
    thickness_nominal = ...
    width_nominal = ...
    length_nominal = ...
    thickness_nominal_frac = ... # Fracciones (6/4, 3 5/8)
    width_nominal_frac = ...
    
    # SECCIÓN 3: DIMENSIONES REALES (Lo que mide la bodega)
    thickness = ...
    width = ...
    length = ...
    pieces = ...
    
    # SECCIÓN 4: VOLÚMENES (Calculados)
    vol_physical_m3 = ...        # Fórmula: t*w*l*p / 1M
    vol_purchase_m3 = ...        # Volumen para compra
    vol_shipment_m3 = ...        # Volumen para exportación
    vol_physical_real_m3 = ...   # Audit trail
    
    # SECCIÓN 5: FINANCIERO
    estimated_cost_usd = ...
    cost_clp_unit = ...
    currency_id = ...
    
    # SECCIÓN 6: EXPORTACIÓN
    board_feet = ...
    vol_mbf = ...
    export_calculation_rule = ...  # 'metric'/'f1550'/'f5085'
    
    # SECCIÓN 7: AUDITORÍA
    audit_snapshot = ...
    audit_hash = ...
```

### Flujo Típico de Línea

```
1. CREATE → lot_name se sanitiza a EAN-13
2. CREATE → Validación de dimensiones (rango check)
3. SAVE → Cálculos de volumen disparan automáticamente
4. USER EDIT → Si cambia dimensiones, volúmenes se recalculan
5. STAGING → Línea lista para transferir a stock.lot
```

---

## 🧪 CÓMO EJECUTAR TESTS

### Opción 1: Directamente en Docker (Recomendado)

```bash
# Terminal 1: Ver logs
docker logs -f odoo18_app

# Terminal 2: Ejecutar tests
docker exec odoo18_app python -m pytest \
  /mnt/extra-addons/madenat_lumber_core/tests/lumber_reception_test.py \
  -v --tb=short

# O ejecutar caso específico
docker exec odoo18_app python -m pytest \
  /mnt/extra-addons/madenat_lumber_core/tests/lumber_reception_test.py::TestLumberReception::test_06_volume_calculations \
  -vv
```

### Opción 2: Desde Python Local

```bash
cd /home/viruco/dev-stack/odoo/odoo-18-ce
python -m pytest custom_addons/madenat_lumber_core/tests/lumber_reception_test.py -v
```

### Opción 3: Test de Instalación en DB Fresca

```bash
# Crea DB nueva, instala módulo, ejecuta tests, limpia DB
docker exec odoo18_app odoo \
  -u madenat_lumber_core \
  -d test_fresh_$(date +%s) \
  --db_host=odoo18_db --db_user=odoo --db_password=odoo \
  --test-enable \
  --stop-after-init
```

---

## 🔍 DEBUGGING COMÚN

### Problema: `vol_physical_m3` no se calcula

**Causa probable:** Campo `pieces` está vacío (default 0)  
**Solución:**
```python
# En create() o write():
if not vals.get('pieces'):
    vals['pieces'] = 1  # Default a 1 pieza
```

### Problema: `lot_name` no se sanitiza

**Causa probable:** El método `create()` no se ejecutó (creación desde SQL)  
**Solución:**
```python
# Llamar manualmente antes de persistir:
line = LumberReceptionLine.new({'lot_name': '123.0'})
line._sanitize_lot_name('123.0')  # Devuelve '0000000000123'
```

### Problema: `_compute_export_values()` devuelve 0

**Causa probable:** `export_calculation_rule` no está definido  
**Solución:**
```python
# Asegurar que está en vals al crear:
vals['export_calculation_rule'] = 'metric'  # o 'f1550' o 'f5085'
```

### Problema: Tests fallan con `ConnectionPool`

**Causa probable:** Container Docker no está corriendo  
**Solución:**
```bash
docker restart odoo18_app
docker ps | grep odoo18_app  # Verificar que esté UP
```

---

## 📝 AGREGAR NUEVO CAMPO

Si necesitas agregar un nuevo campo a `LumberReceptionLine`:

### Paso 1: Determinar la sección
```python
# Decidir qué sección (1-7) pertenece
# Ej: "impuesto_maritimo" → SECCIÓN 5 (Financiero)
```

### Paso 2: Agregarle el campo
```python
class LumberReceptionLine(models.Model):
    # SECCIÓN 5: FINANCIERO
    impuesto_maritimo = fields.Float(
        string="Impuesto Marítimo (USD)",
        default=0.0,
        help="Arancel marítimo aplicado"
    )
```

### Paso 3: Si requiere cálculo
```python
@api.depends('estimated_cost_usd', 'reception_id.customs_rate')
def _compute_impuesto_maritimo(self):
    for line in self:
        rate = line.reception_id.customs_rate or 0.0
        line.impuesto_maritimo = line.estimated_cost_usd * rate
```

### Paso 4: Si requiere validación
```python
def create(self, vals_list):
    for vals in vals_list:
        if vals.get('impuesto_maritimo') < 0:
            raise ValidationError("Impuesto no puede ser negativo")
    return super().create(vals_list)
```

### Paso 5: Agregar test
```python
def test_10_impuesto_maritimo(self):
    """Calcula impuesto marítimo correctamente"""
    recepcion = self.LumberReception.create({
        'name': 'TEST-010',
        'supplier_id': self.supplier.id,
        'customs_rate': 0.05,  # 5%
    })
    linea = self.LumberReceptionLine.create({
        'reception_id': recepcion.id,
        'estimated_cost_usd': 100.0,
    })
    self.assertAlmostEqual(linea.impuesto_maritimo, 5.0)
```

---

## 🔄 AGREGAR NUEVO TEST

### Paso 1: Ubicación
```
/tests/lumber_reception_test.py → TestLumberReception class
```

### Paso 2: Template
```python
def test_10_tu_caso(self):
    """Descripción breve del caso"""
    # Setup
    recepcion = self.LumberReception.create({...})
    linea = self.LumberReceptionLine.create({...})
    
    # Acción
    resultado = linea.mi_metodo()
    
    # Validación
    self.assertEqual(resultado, expected)
```

### Paso 3: Ejecutar
```bash
docker exec odoo18_app python -m pytest \
  .../tests/lumber_reception_test.py::TestLumberReception::test_10_tu_caso \
  -vv
```

---

## 🚀 SUBIR A PRODUCCIÓN

### Pre-checklist

- [ ] Tests pasan: `pytest -v`
- [ ] Docker test pasa: `--test-enable --stop-after-init`
- [ ] Syntax ok: `python -m py_compile models/lumber_reception.py`
- [ ] No hay fields duplicados
- [ ] Manifest está en orden correcto
- [ ] README.md está actualizado
- [ ] Documentación está sincronizada

### Proceso de Deploy

```bash
# 1. En servidor de producción
docker exec odoo18_app odoo \
  -u madenat_lumber_core \
  -d production_db \
  --db_host=db --db_user=odoo --db_password=<password> \
  --stop-after-init

# 2. Verificar en UI
# → Ir a Aplicaciones → Buscar "MADENAT Lumber Core"
# → Debería estar "Instalado" con versión 18.0.4.0.0

# 3. Restart app
docker restart odoo18_app

# 4. Verificar logs
docker logs --tail=100 odoo18_app | grep -i lumber
```

---

## 📂 ESTRUCTURA DE CARPETAS IMPORTANTE

```
/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_core/
├── models/
│   ├── lumber_reception.py       ← AQUÍ está LumberReceptionLine
│   ├── reception_service.py      ← Servicio staging→stock.lot
│   ├── utils_uom.py              ← Conversiones de unidad
│   ├── ingestion_gate.py          ← Gates de validación
│   └── __init__.py
├── tests/
│   ├── lumber_reception_test.py  ← AQUÍ agregar nuevos tests
│   └── __init__.py
├── views/
│   ├── lumber_reception_views.xml ← DEBE cargarse ANTES del menú
│   └── lumber_core_menu.xml       ← DEBE cargarse DESPUÉS de vistas
├── docs/
│   ├── 00_ARQUITECTURA.md         ← Decisiones base
│   ├── HOJA_RUTA_EJECUTIVA.md     ← Estado y progreso
│   ├── 03_TESTS.md                ← Matriz de tests
│   ├── Errores/
│   │   ├── AUDITORIA_2026_05_02.md ← AUDIT COMPLETO (AQUÍ)
│   │   ├── GUIA_CONTINUIDAD_TECNICA.md ← ESTA GUÍA (AQUÍ)
│   │   └── ... otros archivos de error
│   └── README.md
├── wizard/
│   └── lumber_reception_mass_update_views.xml
├── __manifest__.py                ← ⚠️ ORDEN CRÍTICO
└── __init__.py
```

---

## 🎯 PRÓXIMAS TAREAS RECOMENDADAS

### CORTO PLAZO (Esta semana)
1. [ ] Ejecutar todos los tests en ambiente real
2. [ ] Validar en UI que los campos aparezcan correctamente
3. [ ] Crear 3-5 recepciones de prueba manualmente
4. [ ] Verificar que los lotes se creen correctamente en `stock.lot`

### MEDIANO PLAZO (Próximas 2 semanas)
1. [ ] Implementar tests T10-T14 (export rules, currency)
2. [ ] Agregar reportes de trazabilidad
3. [ ] Performance testing con 10k líneas
4. [ ] Dashboard de reconciliación comercial

### LARGO PLAZO (Próximo mes)
1. [ ] Integración con módulo de facturación
2. [ ] Sincronización con sistema de costos
3. [ ] API REST para integraciones externas
4. [ ] Backup/restore procedures

---

## 🆘 DÓNDE BUSCAR AYUDA

| Problema | Archivo |
|----------|---------|
| "¿Cómo funciona X?" | `/docs/00_ARQUITECTURA.md` |
| "¿Qué estado está el módulo?" | `/docs/Errores/AUDITORIA_2026_05_02.md` |
| "¿Cómo agrego un campo?" | Este documento (sección AGREGAR NUEVO CAMPO) |
| "¿Cómo agrego un test?" | Este documento (sección AGREGAR NUEVO TEST) |
| "El código tiene un bug" | `/docs/Errores/INFORME_AUDITORIA_CODIGO.md` |
| "¿Cuáles son los riesgos?" | `/docs/Errores/AUDITORIA_2026_05_02.md` (sección RIESGOS) |
| "¿Qué tests existen?" | `/docs/03_TESTS.md` |

---

## ✨ NOTAS FINALES

- **Este módulo está LISTO para producción** (95%+ completado)
- Fue auditado exhaustivamente el 2 de mayo de 2026
- Tests pasan en Docker sin errores
- Documentación está al día
- Cualquier desarrollador puede continuar desde aquí sin problemas

**Si aún tienes dudas, revisa estos archivos en orden:**
1. `/docs/00_ARQUITECTURA.md`
2. `/docs/Errores/AUDITORIA_2026_05_02.md`
3. Este documento
4. El código mismo (`models/lumber_reception.py`)

¡Buena suerte! 🚀
