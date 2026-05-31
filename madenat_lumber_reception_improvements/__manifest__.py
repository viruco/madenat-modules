# -*- coding: utf-8 -*-
{
    'name': 'MADENAT Lumber Reception Improvements',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Drop Shipment support for lumber reception',
    'description': """
MADENAT Lumber Reception Improvements
======================================

Agrega funcionalidad de Drop Shipment a lumber.reception.

**IMPORTANTE**: Este módulo EXTIENDE lumber.reception sin modificar código existente.
Usa herencia (_inherit) de Odoo para agregar campos y funcionalidades.

Características:
----------------
* Drop Shipment a procesadores terceros
* Campo is_processor en res.partner
* Campos nuevos en lumber.reception (sin tocar existentes)

Instalación:
------------
1. Instalar dependencias (madenat_lumber_purchasing)
2. Actualizar lista de aplicaciones
3. Instalar este módulo
4. NO requiere migración de datos (solo agrega campos nuevos)

Autor: Equipo MADENAT
Fecha: Diciembre 2025
    """,
    'author': 'MADENAT',
    'website': 'https://www.madenat.cl',
    'depends': [
        'base',
        'stock',
        'madenat_lumber_core',
        'madenat_lumber_purchasing',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}