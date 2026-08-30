# -*- coding: utf-8 -*-
"""
Migración 18.0.5.4.0 — post-migrate: Aplicar groups_id de menús Intake

CONTEXTO:
  La política de visibilidad ya fue codificada en XML (groups de menuitems),
  pero Odoo 18 no reaplica `groups_id` a registros `ir.ui.menu` existentes
  mediante el upgrade estándar. Esta migración aplica formalmente en BD el
  reemplazo controlado de `groups_id` para los 4 menús afectados.

POLÍTICA OBJETIVO:
  - Pendientes de Stock, Tablero de Recepciones, Historial de Ingresos:
      exclusively group_madenat_jefatura_operaciones
  - Ajustes Físicos (Stock):
      exclusively stock.group_stock_manager (inventario transversal)

RESTRICCIONES:
  - No toca ACL, record rules, modelos funcionales ni lógica de Intake.
  - No toca: menu_madenat_lumber_intake_wizard, menu_lumber_reception_pending,
    menu_guia_processing_root, menu_guia_processing_list.
  - Idempotente: si ya están correctos, no modifica nada.
  - Usa ORM + XML IDs; aborta con error útil si algún XML ID no existe.
"""
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    group_jefatura = env.ref(
        'madenat_lumber_core.group_madenat_jefatura_operaciones')
    group_stock_manager = env.ref('stock.group_stock_manager')

    targets = {
        'madenat_lumber_core.menu_lumber_reception_pending_stock': group_jefatura,
        'madenat_lumber_core.menu_lumber_reception_kanban': group_jefatura,
        'madenat_lumber_core.menu_lumber_reception': group_jefatura,
        'madenat_lumber_core.menu_madenat_inventory_adjustments': group_stock_manager,
    }

    for xmlid, group in targets.items():
        menu = env.ref(xmlid)
        if menu.groups_id != group:
            # Reemplazo total, nunca append: evita suma accidental de grupos.
            menu.groups_id = [(6, 0, [group.id])]