# MADENAT Lumber Core

> 📖 Documentación canónica: [../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md](../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md)
> Arquitectura vigente: [../madenat_lumber_docs/CANON/00_ARQUITECTURA.md](../madenat_lumber_docs/CANON/00_ARQUITECTURA.md)

**Versión:** `18.0.5.3.0` | **Odoo:** 18 CE | **CHANGELOG:** [CHANGELOG.md](CHANGELOG.md)

Módulo orquestador para la recepción nacional de madera comprada (Guías de Despacho).

## 🚀 Inicio Rápido

Para comenzar inmediatamente, lee: **[WIKI/GUIA_PRODUCCION_FINAL.md](../madenat_lumber_docs/WIKI/GUIA_PRODUCCION_FINAL.md)**

## 📚 Documentación Completa

La documentación canónica reside en `madenat_lumber_docs/`. Estructura recomendada:

1. **[CANON/INDICE_DOCUMENTACION.md](../madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md)** ← Mapa maestro
2. **[CANON/00_ARQUITECTURA.md](../madenat_lumber_docs/CANON/00_ARQUITECTURA.md)** ← Arquitectura y modelos
3. **[WIKI/GUIA_PRODUCCION_FINAL.md](../madenat_lumber_docs/WIKI/GUIA_PRODUCCION_FINAL.md)** ← Guía de producción

## 🎯 Arquitectura Core

- **Gates 0–3 + GB-1:** PreUpload → DocumentReconciliation → CommercialAnalysis → GB-1 inline → PreCommit (notario criptográfico)
- **Gate 3 es el único punto autorizado de escritura en inventario** (AD-04)
- **Staging obligatorio** en `lumber.reception.line` antes de persistir a `stock.lot`

## 📦 Instalación

```bash
docker exec -it odoo18_app odoo -u madenat_lumber_core -d TU_DB --stop-after-init
docker restart odoo18_app
```

## 🔗 Módulos Relacionados

- `madenat.guia.processing` (modelo interno) — Guías de despacho y procesamiento
- `madenat_lumber_costing` — Costeo multi-nivel
- `madenat_lumber_billing` — Facturación y pagos
- `madenat_lumber_shipping_core` — Motonaves y viajes de exportación
- `madenat_lumber_logistics` — Contenedores y embarques
- `madenat_lumber_purchasing` — Compras especializadas
- `madenat_lumber_reports` — Reportes de inventario


---

**Proyecto MADENAT** — Documentación canónica en [madenat_lumber_docs/](../madenat_lumber_docs/)
