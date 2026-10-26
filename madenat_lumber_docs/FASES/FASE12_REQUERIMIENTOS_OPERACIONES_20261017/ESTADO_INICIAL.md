# ESTADO_INICIAL — E0 Verificación de Estado Heredado
**FASE 12 — Requerimientos de Operaciones (Cristhian)**  
**Fecha:** 2026-10-17 | **Agente:** Antigravity | **Solo lectura — cero cambios**

---

## 1. Verificación Git

| Ítem | Esperado | Verificado | Conforme |
|---|---|---|---|
| HEAD | `254e6d3` | `254e6d3e10a67a6c6323c8165e2cf73dc1851f50` | ✅ |
| Rama | `feat/guia-correccion-documental-preservada-20261002` | ídem | ✅ |
| Entradas WIP (`git status`) | 11 | 11 | ✅ |
| Último commit | `docs(canon): AD-110 …` | ídem | ✅ |
| Push al remoto | NUNCA | Sin push | ✅ |

### 1.1 Detalle WIP — Hashes SHA-256

| Modo | Archivo | SHA-256 (primeros 16 hex) |
|---|---|---|
| M | `madenat_lumber_costing/__manifest__.py` | `6082826b361ff5c3` |
| M | `madenat_lumber_costing/models/__init__.py` | `5f4c4223f8119e5d` |
| M | `madenat_lumber_costing/models/lumber_cost_distribution.py` | `579af41826f7e24a` |
| M | `madenat_lumber_costing/models/lumber_shipment_costing.py` | `3e2fdac2a3c9cd68` |
| M | `madenat_lumber_costing/security/ir.model.access.csv` | `28007014901efbaf` |
| M | `madenat_lumber_costing/tests/__init__.py` | `857ab865c49f1a82` |
| M | `madenat_lumber_costing/views/lumber_cost_distribution_views.xml` | `6a785298b73d995d` |
| M | `madenat_lumber_reports/views/lumber_reports_menu.xml` | `4047752ab265ec4f` |
| ?? | `madenat_lumber_costing/models/stock_lot_cost_line.py` | `2e4739928bd8f2fa` |
| ?? | `madenat_lumber_costing/tests/test_shipment_costing_c2.py` | `b9c1ad5939fb8f4f` |
| ?? | `madenat_lumber_costing/views/lumber_shipment_costing_views.xml` | `7e8a1bafa28d0a7d` |

**10 de `madenat_lumber_costing`** = D1 BLOQUEADO. **1 de `madenat_lumber_reports`** = P2-2, origen no demostrado. Ninguno se toca.

---

## 2. Versiones de Módulos

| Módulo | Esperado | Verificado |
|---|---|---|
| `madenat_lumber_logistics` | 18.0.1.36.0 | ✅ |
| `madenat_lumber_core` | 18.0.6.9.0 | ✅ |
| `madenat_lumber_intake` | 18.0.0.15.0 | ✅ |
| `madenat_lumber_shipping_core` | 18.0.1.0.0 | ✅ |

---

## 3. Versiones Documentales

| Documento | Esperado | Verificado |
|---|---|---|
| `CANON/04` (DECISION_LOG) — última AD | AD-110 | ✅ |
| `CANON/19` (IMPUTACION_SV) | 1.33.0 | ✅ |
| `INDICE_DOCUMENTACION.md` | 12.37.0 | ✅ |

---

## 4. Base de Datos Local (madenat_test)

| Ítem | Valor verificado |
|---|---|
| Contenedores Docker | `odoo18_app`, `odoo18_db` activos |
| `stock_lot` total | 151 |
| `stock_quant` con qty > 0 | 105 |
| Guía `4495589` (Arauco) | tipo=granel, state=validated, partner=Maderas Arauco S.A. |
| Guía `95806` | tipo=granel, state=verified, partner=S.I.I. - LOS ANGELES |
| `SV00000000841` en stock_quant | qty=40.3150, location_id=8 (WH/Stock) |

---

## 5. Diferencias Reportadas

### D-E0-1: HOJA_RUTA_EJECUTIVA.md desalineada
- Fecha en archivo: 2026-05-23. Prioridades: largo/unidades, T29–T32 (pre-FASE10).
- No refleja FASE10/11 ni requerimientos R1–R8.
- **Impacto:** solo documental → WP-G.

### D-E0-2: _CAPSULA_CONTEXTO.md desalineada
- Fecha: 2026-05-30. Costing/reports como "pendiente de inventario".
- **Impacto:** solo documental → WP-G.

### D-E0-3: Guía 95806 — partner inesperado
- Estado heredado menciona proveedor JCE; en DB el partner es `S.I.I. - LOS ANGELES`.
- Hipótesis: asociación con SII en lugar del proveedor real. Se notifica sin modificar.
- **Impacto:** WP-C (visibilidad por proveedor).

---

## 6. Criterio de Salida E0: CUMPLIDO

- [x] HEAD = `254e6d3` ✅  
- [x] 11 entradas WIP con hashes SHA-256 ✅  
- [x] Versiones de módulos y documentos correctas ✅  
- [x] DB local accesible; datos protegidos intactos ✅  
- [x] Diferencias D-E0-1/2/3 reportadas ✅  
- [x] CERO cambios en código, datos o repositorio ✅
