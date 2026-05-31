# Árbol de Dependencias entre Módulos MADENAT

**Módulo:** madenat_lumber_core / madenat_lumber_*
**Categoría:** Técnico
**Estado:** Activo
**Última actualización:** 2026-05-30

---

## Propósito

Documentar las dependencias entre módulos propios y módulos base de Odoo para evitar errores de instalación, actualización y migración.

---

## Árbol de dependencias

```
odoo_base (base)
├── stock
│   ├── purchase ──────────────┐
│   ├── mail ────────────┐     │
│   └── product ──────┐  │     │
│                     ▼  ▼     ▼
├── account ───────────────────────┐
│                                  ▼
└── uom ───────────────────────┐   │
                               ▼   ▼
                    madenat_lumber_shipping_core  ← datos maestros marítimos
                     (base, mail, uom)           │
                               │                 │
                               ▼                 ▼
                        madenat_lumber_core  ← módulo base maderero
                        (stock, product, purchase, account, mail, sms)
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
    madenat_lumber_purchasing   madenat_lumber_logistics
    (purchase, core)            (base, stock, mail,
               │                 core, shipping_core)
               ▼               │
    madenat_lumber_reception_  ├──► madenat_lumber_billing
    improvements               │   (base, account, base_automation,
    (base, stock, core,        │    stock, core, logistics)
     purchasing)               │
                               └──► madenat_lumber_costing
                                    (account, core, logistics,
                                     shipping_core)
```

---

## Dependencias de cada módulo

### madenat_lumber_shipping_core (dependencia externa)

| Módulo Odoo | Razón |
|---|---|
| `base` | Modelos base, res.partner, res.company |
| `mail` | mail.thread, mail.activity.mixin |
| `uom` | Unidades de medida para capacidad marítima |

> **Nota:** Este módulo proporciona los datos maestros de transporte marítimo (barcos, viajes, reservas). No depende de ningún otro módulo MADENAT. Es prerequisito de `madenat_lumber_logistics` y `madenat_lumber_costing`.

---

### madenat_lumber_core

| Módulo Odoo | Razón |
|---|---|
| `stock` | stock.lot, stock.picking, stock.move |
| `product` | product.template, product.product |
| `purchase` | purchase.order, purchase.order.line |
| `account` | account.move (facturas) |
| `mail` | mail.thread, mail.activity.mixin |
| `sms` | Notificaciones SMS |

> **Nota:** Módulo base de la suite maderera. Todos los demás módulos MADENAT dependen de él directa o indirectamente.

---

### madenat_lumber_purchasing

| Módulo Odoo | Razón |
|---|---|
| `purchase` | Extiende órdenes de compra para madera |
| `madenat_lumber_core` | Modelos propios de recepción y lotes |

---

### madenat_lumber_reception_improvements

| Módulo Odoo | Razón |
|---|---|
| `base` | Modelos base, res.partner |
| `stock` | Operaciones de inventario |
| `madenat_lumber_core` | lumber.reception (modelo base) |
| `madenat_lumber_purchasing` | Extiende flujo de compras |

---

### madenat_lumber_logistics

| Módulo Odoo | Razón |
|---|---|
| `base` | Modelos base |
| `stock` | Contenedores, movimientos de stock |
| `mail` | Tracking y comunicación |
| `madenat_lumber_core` | Lotes de madera, recepciones |
| `madenat_lumber_shipping_core` | Barcos, viajes, reservas marítimas |

---

### madenat_lumber_billing

| Módulo Odoo | Razón |
|---|---|
| `base` | Modelos base |
| `account` | Facturación en Odoo Accounting |
| `base_automation` | Flujos de trabajo automatizados |
| `stock` | Datos de embarques |
| `madenat_lumber_core` | Modelos propios de madera |
| `madenat_lumber_logistics` | Datos de contenedores y embarques |

---

### madenat_lumber_costing

| Módulo Odoo | Razón |
|---|---|
| `account` | Cuentas contables, valorización |
| `madenat_lumber_core` | Lotes de madera |
| `madenat_lumber_logistics` | Costos logísticos de embarque |
| `madenat_lumber_shipping_core` | Datos de transporte marítimo |

---

## Orden de instalación

Para una instalación limpia, seguir este orden:

1. **Módulos base de Odoo:** `base`, `stock`, `product`, `purchase`, `account`, `mail`, `sms`, `uom`, `base_automation`
2. **madenat_lumber_shipping_core** (prerequisito externo)
3. **madenat_lumber_core** (módulo base maderero)
4. **madenat_lumber_purchasing**
5. **madenat_lumber_reception_improvements**
6. **madenat_lumber_logistics**
7. **madenat_lumber_billing**
8. **madenat_lumber_costing**

> **Nota:** Los módulos 4–5 pueden instalarse en paralelo con el 6–7–8, siempre que `core` y `shipping_core` ya estén instalados.

---

## Restricciones conocidas

- En Odoo 18 CE, `sale` no es dependencia de MADENAT porque el flujo de venta se gestiona directamente desde `stock` y `account`.
- `madenat_lumber_shipping_core` es un módulo externo requerido — no instalar `logistics` ni `costing` sin él.
- `madenat_lumber_costing` depende de `shipping_core` directamente (no solo a través de `logistics`), por lo que ambos deben estar presentes.

---

## Relacionado

- [[modulo_lumber_core]]
- [[00_ARQUITECTURA]]
- [[despliegue_modulo]]
