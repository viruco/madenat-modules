# Gates de Validación — Pipeline de Ingesta MADENAT

**Módulo:** `madenat_lumber_core.models.ingestion_gate`  
**Versión:** 1.2.0  
**Última actualización:** 2026-06-02  
**Responsable:** Pipeline de validación inmutable

---

## Propósito

Los Gates de Validación forman el núcleo del pipeline de ingesta de MADENAT. Cada gate valida un aspecto específico del flujo de recepción sin modificar datos, garantizando que solo datos coherentes y conformes lleguen al inventario real.

**Principio fundamental:** Gates **NUNCA escriben** en la base de datos. Responsabilidad única: validar.

---

## Arquitectura General

```
                    ENTRADA
                       ↓
        ┌───────────────────────────┐
        │   GATE 0: PRE-UPLOAD      │
        │  (Validación de archivos) │
        └───────────────┬───────────┘
                        ↓
        ┌───────────────────────────────────┐
        │  GATE 1: DOC RECONCILIATION       │
        │  (Reconciliación PDF vs Excel)    │
        └───────────────┬───────────────────┘
                        ↓
        ┌────────────────────────────────────┐
        │  GATE 2: COMMERCIAL ANALYSIS       │
        │  (Validación de lotes en staging)  │
        └───────────────┬────────────────────┘
                        ↓
        ┌──────────────────────────────────┐
        │  GATE 3: PRE-COMMIT              │
        │  (Firma criptográfica SHA-256)   │
        └──────────────┬───────────────────┘
                       ↓
                  [COMMIT BD]
```

---

## Gate 0: Pre-Upload (Validación de Archivos)

**Clase:** `Gate0PreUpload`  
**Punto de activación:** Antes de parsear archivos cargados  
**Entrada:** Nombre de archivo, bytes, tipo esperado (excel|pdf)  
**Salida:** `ValidationResult` (errores bloqueantes)

### Responsabilidades

1. Validar extensión de archivo
   - `.xlsx`, `.xls` para Excel
   - `.pdf` para PDF
   
2. Validar tamaño
   - Mínimo: > 0 bytes
   - Máximo: ≤ 20 MB
   
3. Validar coherencia de tipo
   - Si se espera Excel, verificar que sea Excel
   - Si se espera PDF, verificar que sea PDF

### Constantes

```python
EXTENSIONES_EXCEL = {".xlsx", ".xls"}
EXTENSIONES_PDF   = {".pdf"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
```

### Errores que genera

| Código de error | Mensaje | Severidad |
|---|---|---|
| `FILE_EXTENSION_INVALID` | El archivo no es del tipo esperado | Bloqueante |
| `FILE_EMPTY` | El archivo está vacío | Bloqueante |
| `FILE_TOO_LARGE` | Archivo supera 20 MB | Bloqueante |

### Ejemplo de uso

```python
from .ingestion_gate import Gate0PreUpload

gate0 = Gate0PreUpload()

# Validar Excel
result_excel = gate0.validate("datos.xlsx", excel_bytes, "excel")
if not result_excel.is_valid:
    raise UserError(result_excel.user_message)

# Validar PDF
result_pdf = gate0.validate("guia.pdf", pdf_bytes, "pdf")
if not result_pdf.is_valid:
    raise UserError(result_pdf.user_message)
```

---

## Gate 1: Document Reconciliation (Reconciliación Documental)

**Clase:** `Gate1DocumentReconciliation`  
**Punto de activación:** Después de parsear Excel y PDF  
**Entrada:** Dict de datos Excel, Dict de datos PDF, OC ID (opcional)  
**Salida:** `ValidationResult` (errores bloqueantes + warnings)

### Responsabilidades

1. **Reconciliar Nro de Guía**
   - Normalizar número de guía de ambas fuentes
   - Verificar coincidencia exacta
   - Ignora prefijos como "GUÍA", "NRO", "N°"
   
2. **Reconciliar Volumen Total**
   - Comparar volumen declarado en Excel vs PDF
   - Usar tolerancia configurable (default: 2%)
   - Detectar discrepancias potenciales
   
3. **Validar Tipo de Cambio**
   - Comparar tipo de cambio entre fuentes
   - Usar tolerancia configurable (default: ±20%)
   - Generar **warning** (no bloqueante) si diverge

### Constructor

```python
gate1 = Gate1DocumentReconciliation(
    env=self.env,
    tolerancia_volumen=0.02,        # 2% (default)
    tolerancia_tipo_cambio=0.20     # ±20% (default)
)
```

### Métodos principales

#### `validate(excel_data, pdf_data, oc_id=None)`

Ejecuta las 3 reconciliaciones. Retorna `ValidationResult`.

```python
result = gate1.validate(
    excel_data={'nro_guia': '12345', 'total_vol_m3': 15.5, 'tipo_cambio': 3.85},
    pdf_data={'nro_guia': '12345', 'total_vol_m3': 15.4, 'tipo_cambio': 3.90}
)

if not result.is_valid:
    raise UserError(result.user_message)

if result.has_warnings:
    # Mostrar advertencias pero permitir continuar con confirmación
    self.ingestion_warnings = result.user_message
```

### Errores y Warnings

| Código | Tipo | Mensaje | Acción |
|---|---|---|---|
| `NROGUIA_MISMATCH` | Error | Guía no coincide Excel ≠ PDF | Bloqueante |
| `VOLUMEN_MISMATCH` | Error | Volumen diferencia > tolerancia | Bloqueante |
| `TIPO_CAMBIO_OUT_OF_RANGE` | Warning | Tipo de cambio diverge significativamente | Requiere confirmación |

### Internals (normalizaciones)

- **Guía:** Elimina "GUÍA", "GUÍA", "NRO", "N°", "Nº"; normaliza espacios; elimina puntos
- **Volumen:** Convierte a float; maneja comas como decimales
- **Tipo Cambio:** Convierte a float; maneja variaciones de formato

---

## Gate 2: Commercial Analysis (Análisis Comercial)

**Clase:** `Gate2CommercialAnalysis`  
**Punto de activación:** Después de parsear staging (`lumber.reception.line`)  
**Entrada:** Lista de líneas de staging  
**Salida:** `ValidationResult` (errores bloqueantes)

### Responsabilidades

1. **Validar no vacío**
   - Verificar que existan líneas para procesar
   
2. **Validar dimensiones nominales por lote**
   - Espesor nominal > 0
   - Ancho nominal > 0
   
3. **Validar subproducto configurado**
   - Cada lote debe tener subproducto
   
4. **Validar catálogo de producto**
   - Cada lote debe tener producto catálogo vinculado

### Constructor

```python
gate2 = Gate2CommercialAnalysis(env=self.env, tolerancia_volumen=0.02)
```

### Método principal

#### `validate(staging_lines)`

Itera cada línea de staging y aplica validaciones.

```python
staging = reception.reception_line_ids
result = gate2.validate(staging)

if not result.is_valid:
    raise UserError(result.user_message)
```

### Errores

| Código | Lote | Severidad |
|---|---|---|
| `EMPTY_STAGING` | N/A | Bloqueante |
| `NOMINAL_THICKNESS_INVALID` | Por lote | Bloqueante |
| `NOMINAL_WIDTH_INVALID` | Por lote | Bloqueante |
| `SUBPRODUCT_MISSING` | Por lote | Bloqueante |
| `PRODUCT_NOT_FOUND` | Por lote | Bloqueante |

### Ejemplo

```python
result = gate2.validate(reception.reception_line_ids)

# Salida en caso de error:
# ⛔ No se puede continuar. Se encontraron los siguientes problemas:
#   • [NOMINAL_THICKNESS_INVALID] (campo: thickness_nominal) 
#     Lote L-001: Espesor nominal <= 0.
#   • [SUBPRODUCT_MISSING] (campo: subproduct_id) 
#     Lote L-002: Sin subproducto definido.
```

---

## Gate 3: Pre-Commit (Notario Criptográfico)

**Clase:** `Gate3PreCommit`  
**Punto de activación:** Inmediatamente antes de escribir en BD  
**Entrada:** Recepción + líneas de staging  
**Salida:** (snapshot JSON, firma SHA-256)

### Responsabilidades

1. **Generar snapshot inmutable**
   - Captura estado exacto: reception, operador, timestamp, lotes
   
2. **Generar firma criptográfica**
   - SHA-256 del snapshot
   - Garantiza que nadie alteró datos entre validación y commit

### Constructor

```python
gate3 = Gate3PreCommit(env=self.env)
```

### Método principal

#### `generate_signature(reception, staging_lines)`

Retorna tupla `(json_snapshot, sha256_hash)`.

```python
snapshot_json, signature_hash = gate3.generate_signature(reception, staging)

# Guardar para auditoría:
reception.write({
    'signature_hash': signature_hash,
    'snapshot_json': snapshot_json
})
```

### Estructura del Snapshot

```json
{
  "reception_id": 1234,
  "guide_no": "REC-2026-06-02-0001",
  "timestamp_utc": "2026-06-02T16:37:15.123456",
  "operator_id": 42,
  "total_commercial_m3": 25.5,
  "lines": [
    {
      "lot_name": "L-001",
      "vol_purchase_m3": 12.3,
      "vol_shipment_m3": 12.0,
      "pieces": 180
    }
  ]
}
```

---

## Flujo de Integración Completo

En `lumber_reception.py → action_process_files()`:

```python
from .ingestion_gate import (
    Gate0PreUpload,
    Gate1DocumentReconciliation,
    Gate2CommercialAnalysis,
    Gate3PreCommit
)

def action_process_files(self):
    """Procesa archivos a través de los 3 gates de validación."""
    
    # --- GATE 0: Validar archivos crudos ---
    gate0 = Gate0PreUpload()
    for fname, fbytes, ftype in [
        (self.excel_filename, self.excel_file, "excel"),
        (self.pdf_filename, self.pdf_file, "pdf")
    ]:
        result = gate0.validate(fname, fbytes, ftype)
        if not result.is_valid:
            raise UserError(result.user_message)
    
    # --- Parsear archivos (código existente) ---
    excel_data = self._parse_excel(self.excel_file)
    pdf_data = self._parse_pdf(self.pdf_file)
    
    # --- GATE 1: Reconciliar documentos ---
    gate1 = Gate1DocumentReconciliation(self.env)
    result = gate1.validate(excel_data, pdf_data, oc_id=self.purchase_order_id.id)
    if not result.is_valid:
        raise UserError(result.user_message)
    if result.has_warnings:
        self.ingestion_warnings = result.user_message
        # Mostrar warning en UI; operador confirma antes de continuar
    
    # --- Parsear a staging ---
    self._parse_to_staging(excel_data, pdf_data)
    
    # --- GATE 2: Validar staging comercial ---
    gate2 = Gate2CommercialAnalysis(self.env)
    result = gate2.validate(self.reception_line_ids)
    if not result.is_valid:
        raise UserError(result.user_message)
    
    # --- GATE 3: Generar firma antes de commit ---
    gate3 = Gate3PreCommit(self.env)
    snapshot, signature = gate3.generate_signature(self, self.reception_line_ids)
    self.write({
        'snapshot_json': snapshot,
        'signature_hash': signature
    })
    
    # --- COMMIT: Crear stock.lot real ---
    service = LumberReceptionService(self.env)
    service.create_lots_from_staging(self)
    service.create_stock_picking(self)
    
    self.state = 'processed'
```

---

## Estructura de ValidationResult

Clase que encapsula errores, warnings y generación de mensajes:

```python
@dataclass
class ValidationResult:
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    
    def add_error(code: str, message: str, field: str = None) -> "ValidationResult"
    def add_warning(code: str, message: str, field: str = None) -> "ValidationResult"
    
    @property
    def is_valid() -> bool:  # True si errors es vacío
    
    @property
    def has_warnings() -> bool:  # True si warnings no es vacío
    
    @property
    def user_message() -> str:  # Mensaje formateado para UI
    
    @property
    def audit_summary() -> str:  # Resumen técnico: "errors=2 warnings=1 valid=False"
```

---

## Decisiones de Diseño

### 1. Gates nunca escriben
- Garantiza que la BD es única fuente de verdad
- Facilita reproducción de errores
- Permite rollback sin side effects

### 2. Estructura de errores y warnings
- **Error:** bloquea flujo
- **Warning:** requiere confirmación operador pero no bloquea

### 3. Normalización de datos
- Se aplica en gates, no en modelos
- Reutilizable entre múltiples fuentes
- Centralizado en métodos `_normalize_*`

### 4. Tolerancias paramétricas
- Gate 1 y 2 aceptan tolerancias en constructor
- Default alineado con política comercial
- Modificable sin cambiar código

### 5. Auditoría criptográfica (Gate 3)
- SHA-256 garantiza inmutabilidad
- Snapshot captura estado exacto pre-commit
- Registra operador y timestamp UTC

---

## Riesgos y Mitigación

| Riesgo | Mitigación |
|---|---|
| Gate 1 tolerancias inadecuadas | Parámetros configurables; ajustar según política |
| Gate 2 no detecta subproducto inválido | Gate 2 valida existencia, no coherencia de tipo |
| Gate 3 overhead performance | SHA-256 es rápido; aplicar lazy si volúmenes muy altos |
| Mensajes de error no comprensibles | Usar `user_message` con formato; incluir referencias exactas |

---

## Próximos pasos

- [ ] Integrar gates en `action_process_files()` de `lumber_reception.py`
- [ ] Testear gates con datos reales de recepciones fallidas
- [ ] Documentar casos de uso específicos en `03_TESTS.md`
- [ ] Considerar parametrización de tolerancias en configuración de módulo
