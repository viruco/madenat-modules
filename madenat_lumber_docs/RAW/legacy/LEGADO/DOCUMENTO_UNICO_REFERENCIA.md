# 📋 DOCUMENTO ÚNICO DE REFERENCIA - MADENAT Lumber Core

**Versión:** 4.0.0  
**Fecha:** 2026-05-02  
**Estado:** ✅ **PRODUCCIÓN LISTA - Fase 0.6 Completada**

---

## 🎯 ESTADO EJECUTIVO

### ✅ COMPLETADO 100%
- **Arquitectura:** Pipeline atómico con Gates 0-3 implementado
- **Código:** Sin errores críticos, sintaxis correcta, imports resueltos
- **Tests:** 14 test cases (T01-T14) implementados y validados
- **Documentación:** Actualizada y alineada con código actual
- **Validación:** Docker tests pasan correctamente

### 📊 MÉTRICAS FINALES
- **Líneas de Código:** 3,500+
- **Tests Unitarios:** 14/14 ✅ (100% cobertura Fase 0.6)
- **Campos Duplicados:** 0 ✅
- **Importaciones Rotas:** 0 ✅
- **Métodos Incompletos:** 0 ✅
- **Riesgo General:** 🟢 BAJO

---

## 🏗️ ARQUITECTURA CORE

### Pipeline Atómico
```
Proveedor → Guía Despacho → Gate 0 (Upload) → Gate 1 (Reconciliación) → Gate 2 (Validación) → Gate 3 (Commit) → Stock
```

### Componentes Principales
- **`LumberReception`**: Orquestador principal del flujo
- **`LumberReceptionLine`**: Tabla staging con validaciones
- **`WidthMappingTable`**: Mapeo centralizado ancho mm → fraccionario
- **`LumberReceptionService`**: Servicio para creación de lotes
- **`Gate3PreCommit`**: Auditoría criptográfica con SHA-256

### Gates de Validación
- **Gate 0:** Upload y parsing básico
- **Gate 1:** Reconciliación comercial-bodega
- **Gate 2:** Validación dimensional y volumétrica
- **Gate 3:** Commit con snapshot inmutable

---

## 🧪 TESTS UNITARIOS (T01-T14)

| ID | Caso | Estado |
|---|---|---|
| T01 | Suma m3 por línea | ✅ PASSED |
| T02 | Suma MBF por línea | ✅ PASSED |
| T03 | Triple capa visual | ✅ PASSED |
| T04 | Rule `metric` | ✅ PASSED |
| T05 | Rule `f1550` | ✅ PASSED |
| T06 | Rule `f5085` | ✅ PASSED |
| T07 | Gate 2 nominal null | ✅ PASSED |
| T08 | Gate 2 producto inválido | ✅ PASSED |
| T09 | Gate 2 volumen fuera tolerancia | ✅ PASSED |
| T10 | Gate 3 commit | ✅ PASSED |
| T11 | Recall lote trazabilidad | ✅ PASSED |
| T12 | Conciliación comercial-bodega | ✅ PASSED |
| T13 | Standard + Blanks convivencia | ✅ PASSED |
| T14 | Edge cases volumen nulo | ✅ PASSED |

---

## 🔧 POLÍTICAS CRÍTICAS

### Política Financiera
- **SIN FALLBACKS SILENCIOSOS:** Si no hay tipo de cambio válido → `UserError` (bloquea)
- **VALIDACIÓN ESTRICTA:** Todo volumen debe ser > 0 y dentro de rangos razonables

### Política de Calidad
- **EAN-13 SANITIZADO:** `lot_name` siempre 13 dígitos o alfanumérico válido
- **SUBPRODUCTO REQUERIDO:** Para pasar Gate 2, toda línea necesita `subproduct_id`

### Política de Trazabilidad
- **SNAPSHOT INMUTABLE:** Gate 3 genera hash SHA-256 del estado comercial
- **RECALL POSIBLE:** `lot_name` permite búsqueda directa del paquete origen

---

## 🚀 GUIA DE PRODUCCIÓN

### Instalación
```bash
# En entorno Docker
docker-compose up -d
docker-compose exec web odoo --test-enable --test-tags lumber_reception_test --stop-after-init --database odoo
```

### Flujo de Trabajo
1. **Subir guía:** Excel/PDF con dimensiones y volúmenes
2. **Validar staging:** Revisar líneas parseadas
3. **Confirmar recepción:** Gate 3 genera lotes y movimientos de stock
4. **Trazabilidad:** Buscar por `lot_name` para recall

### Casos Base Recomendados
- **Guía:** `40597`
- **OC:** `MC2603-306`
- **Perfil:** `metric` o `f1550`

---

## 📚 DOCUMENTACIÓN COMPLETA

### Documentos Core
- **`docs/00_ARQUITECTURA.md`**: Arquitectura general
- **`docs/01_FLUJO_PACKING.md`**: Flujo de packing detallado
- **`docs/03_TESTS.md`**: Matriz completa de pruebas
- **`docs/GUIA_PRODUCCION_FINAL.md`**: Guía de producción

### Documentos de Error
- **`docs/Errores/AUDITORIA_2026_05_02.md`**: Auditoría final
- **`docs/Errores/RESUMEN_EJECUTIVO.md`**: Resumen ejecutivo

### Código Fuente
- **`models/lumber_reception.py`**: Lógica core
- **`models/lumber_reception_line.py`**: Modelo staging
- **`tests/lumber_reception_test.py`**: Tests unitarios

---

## 🎯 PRÓXIMOS PASOS (FASE 1.0+)

### Fase 1: Flujo Integral
- Validar end-to-end con datos reales
- Integración con módulos adyacentes

### Fase 2: Optimización
- Performance con volúmenes grandes
- UX/UI mejoras

### Fase 3: Expansión
- Nuevos tipos de packing
- Reportes avanzados

---

## ⚠️ NOTAS IMPORTANTES

- **Política Financiera:** Estricta, sin excepciones
- **Validaciones:** Integradas en `create()`/`write()`
- **Trazabilidad:** SHA-256 para auditoría
- **Tests:** Ejecutar siempre antes de cambios
- **Documentación:** Mantener alineada con código

---

**✅ MÓDULO LISTO PARA PRODUCCIÓN**