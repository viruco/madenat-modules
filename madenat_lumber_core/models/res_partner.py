# -*- coding: utf-8 -*-
"""Extensión ligera de res.partner para auditoría de creaciones automáticas.

FIX 2026-08-21 (Auditoría 11 — proveedor documental):
- `is_auto_created`: bandera de trazabilidad para Contabilidad (María Victoria).
  Se marca cuando un partner es creado automáticamente desde el documento
  (guía PDF) en `madenat.guia.processing`. El campo es informativo/auditable;
  no altera el comportamiento comercial de res.partner.
"""
from odoo import fields, models


class ResPartnerMadenat(models.Model):
    _inherit = 'res.partner'

    is_auto_created = fields.Boolean(
        string='Creado automáticamente',
        default=False,
        copy=False,
        help='Bandera de auditoría: True si el partner fue creado automáticamente '
             'desde un documento de ingesta (guía/PDF). Verificar y completar '
             'datos fiscales antes del cierre financiero (Fase 5).',
    )