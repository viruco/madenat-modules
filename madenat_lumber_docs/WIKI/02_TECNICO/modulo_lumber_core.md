# Módulo madenat_lumber_core

**Módulo:** madenat_lumber_core
**Categoría:** Técnico
**Estado:** Activo — versión 18.0.5.0.0
**Última actualización:** 2026-05-28

---

## Propósito

Documentar la arquitectura interna, estructura de archivos y componentes del módulo principal de MADENAT.

---

## Versión actual

`18.0.5.0.0` — refactor modular aplicado el 2026-05-03.

---

## Estructura de archivos

```
madenat_lumber_core/
├── __init__.py
├── __manifest__.py          ← license LGPL-3 declarado (fix INC-005)
├── models/
│   └── ...
├── views/
│   ├── madenat_res_config_settings_views.xml
│   ├── madenat_subproducto_views.xml
│   ├── stock_lot_views.xml
│   ├── stock_picking_views.xml
│   ├── stock_lot_actions.xml
│   ├── guia_processing_views.xml
│   ├── guia_processing_list_search.xml
│   ├── lumber_reception_views.xml
│   └── lumber_core_menu.xml
├── wizard/
│   ├── lumber_reception_mass_update_views.xml
│   └── madenat_guia_mass_update_views.xml
├── security/
│   ├── madenat_security.xml
│   └── ir.model.access.csv
├── data/
│   └── madenat_subproducto_data.xml
└── reports/
    ├── madenat_guia_report.xml
    └── madenat_guia_report_templates.xml
```

---

## Dependencias declaradas en manifest

```python
'depends': [
    'stock',
    'product',
    'purchase',
    'account',
    'mail',
    'sms',
]
```

---

## Restricciones conocidas

- `mail` es dependencia por `mail.thread` y `mail.activity.mixin`.
- El tracking de `mail.thread` generó problemas de duplicado (ver [[tracking_mail_thread]]).
- La licencia `LGPL-3` debe estar declarada en `__manifest__.py` (ver [[INC-005_license_manifest]]).

---

## Relacionado

- [[dependencias_modulos]]
- [[tracking_mail_thread]]
- [[herencia_odoo_modelos]]
- [[00_ARQUITECTURA]]
