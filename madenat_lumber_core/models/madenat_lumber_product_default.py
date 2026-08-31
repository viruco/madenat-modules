# -*- coding: utf-8 -*-
"""
PRODUCTO MAESTRO POR TIPO DE INGRESO (Fase 1 — Fundación)

Modelo persistente que resuelve el `product_id` fijo por tipo de ingreso
(bruta / procesado), desacoplado de lo que traiga el Excel o la guía.

- No se hardcodea ningún nombre ni ID de producto en Python.
- El helper de lectura es `madenat.ingestion.config.get_default_product`.
- La ambigüedad (dos reglas activas para el mismo tipo/perfil/compañía)
  se bloquea con una validación `@api.constrains`.
"""
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MadenatLumberProductDefault(models.Model):
    _name = 'madenat.lumber.product.default'
    _description = 'Producto Maestro por Tipo de Ingreso'
    _order = 'sequence, id'

    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True,
        help='Identificación legible de la regla (autogenerada).',
    )

    tipo_ingreso = fields.Selection(
        selection=[
            ('bruta', 'Madera Bruta / Compra'),
            ('procesado', 'Madera Procesada / Servicio'),
        ],
        string='Tipo de Ingreso',
        required=True,
        index=True,
        help='Flujo de ingesta al que aplica esta regla de producto maestro.',
    )

    ingestion_profile = fields.Selection(
        selection=[
            ('f5085', 'Madera Bruta — Grado Clear'),
            ('f1550', 'Madera Aserrada S2S'),
            ('blanks', 'Blanks — Legado (métrico/imperial híbrido)'),
            ('metric', 'Madera Bruta — Sistema Métrico'),
        ],
        string='Perfil de Ingesta',
        help='Opcional. Si se indica, la regla refina el producto maestro '
             'para ese perfil específico; si queda vacío, actúa como '
             'fallback del tipo de ingreso.',
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Producto Maestro',
        required=True,
        help='Producto fijo que se asignará a las líneas/lotes de este tipo '
             'de ingreso. No varía según lo que traiga el Excel.',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Compañía',
        help='Opcional. Si se indica, la regla aplica solo a esa compañía; '
             'si queda vacío, es una regla global.',
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Desmarque para deshabilitar esta regla sin eliminarla.',
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de prioridad ante reglas equivalentes.',
    )

    @api.depends('tipo_ingreso', 'ingestion_profile', 'product_id', 'company_id')
    def _compute_name(self):
        tipo_labels = dict(self._fields['tipo_ingreso'].selection)
        profile_labels = dict(self._fields['ingestion_profile'].selection)
        for rec in self:
            tipo = tipo_labels.get(rec.tipo_ingreso, rec.tipo_ingreso or '')
            perfil = profile_labels.get(rec.ingestion_profile, '') if rec.ingestion_profile else ''
            producto = rec.product_id.display_name if rec.product_id else 'Sin producto'
            compania = rec.company_id.name if rec.company_id else 'Global'
            parts = [f'[{tipo}]']
            if perfil:
                parts.append(perfil)
            parts.append(f'→ {producto} ({compania})')
            rec.name = ' '.join(parts)

    @api.constrains('tipo_ingreso', 'ingestion_profile', 'company_id', 'active')
    def _check_no_ambiguous_active_rule(self):
        """Impide dos reglas activas ambiguas para el mismo tipo/perfil/compañía."""
        for rec in self:
            if not rec.active:
                continue
            domain = [
                ('id', '!=', rec.id),
                ('tipo_ingreso', '=', rec.tipo_ingreso),
                ('ingestion_profile', '=', rec.ingestion_profile),
                ('company_id', '=', rec.company_id.id),
                ('active', '=', True),
            ]
            duplicate = self.search(domain, limit=1)
            if duplicate:
                perfil = (' con perfil "%s"' % rec.ingestion_profile) if rec.ingestion_profile else ''
                compania = (' en la compañía "%s"' % rec.company_id.name) if rec.company_id else ' (global)'
                raise ValidationError(_(
                    'Ya existe una regla activa para el tipo de ingreso '
                    '"%(tipo)s"%(perfil)s%(compania)s.\n\n'
                    'Regla existente: %(existente)s\n\n'
                    'Archive o modifique la regla existente antes de crear '
                    'otra con la misma combinación.'
                ) % {
                    'tipo': rec.tipo_ingreso,
                    'perfil': perfil,
                    'compania': compania,
                    'existente': duplicate.display_name,
                })
