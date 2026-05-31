# MADENAT Lumber Core

**Versión:** 5.0.0 | **Odoo:** 18 CE | **Estado:** 🟢 **PRODUCTION READY**

Módulo orquestador para la recepción nacional de madera comprada (Guías de Despacho).

## 🚀 Inicio Rápido

Para comenzar inmediatamente, lee: **[docs/GUIA_PRODUCCION_FINAL.md](docs/GUIA_PRODUCCION_FINAL.md)**

Este documento contiene todo lo necesario para entender y desplegar el módulo.

## 📚 Documentación Completa

Toda la documentación técnica consolidada vive en `docs/`. Estructura recomendada:

1. **[docs/GUIA_PRODUCCION_FINAL.md](docs/GUIA_PRODUCCION_FINAL.md)** ← Documento principal para producción
2. **[docs/00_ARQUITECTURA.md](docs/00_ARQUITECTURA.md)** ← Decisiones arquitectónicas
3. **[docs/INDICE_DOCUMENTACION.md](docs/INDICE_DOCUMENTACION.md)** ← Mapa completo de documentación

## 🎯 Arquitectura Core

- **Pipeline Atómico:** Gates 0-3 con validación criptográfica
- **Shared Kernel:** Validaciones centralizadas en mixins
- **Staging Obligatorio:** Antes de persistir a stock.lot y stock.picking

## 📦 Instalación

```bash
docker exec -it odoo18_app odoo -u madenat_lumber_core -d TU_DB --stop-after-init
docker restart odoo18_app
```

## 🔗 Módulos Relacionados

- `madenat_guia_processing` - Servicio/proceso sobre madera existente
- `madenat_lumber_costing` - Costeo multi-nivel
- `madenat_lumber_billing` - Facturación y pagos
- `madenat_lumber_shipping_core` - Motonaves y viajes de exportación

---

**Proyecto MADENAT** — Documentación consolidada en `docs/`
