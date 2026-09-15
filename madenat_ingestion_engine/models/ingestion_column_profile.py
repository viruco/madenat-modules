# -*- coding: utf-8 -*-
from odoo import fields, models


class MadenatIngestionColumnProfile(models.Model):
    """Perfil de mapeo de columnas para documentos de ingreso de madera.
    
    ESTADO ACTUAL: Esqueleto de configuración. Sin lógica de mapeo de columnas
    todavía.
    
    Los mapeos reales (qué columna del Excel corresponde a qué campo del
    contrato) se diseñarán en una sesión posterior, tras confirmar con
    evidencia real los formatos de los documentos actuales de ingreso.
    """
    
    _name = 'madenat.ingestion.column.profile'
    _description = 'Perfil de mapeo de columnas para documentos de ingreso'
    _order = 'sequence, id'

    name = fields.Char(
        string='Nombre del Perfil',
        required=True,
        help='Identificador único del perfil (ej: "Excel Estándar MADENAT 2026")'
    )
    
    sequence = fields.Integer(
        default=10,
        help='Orden de aparición en listas; menor número = más prioritario'
    )
    
    active = fields.Boolean(
        default=True,
        help='Perfiles inactivos no se usarán en nuevas extracciones'
    )
    
    notes = fields.Text(
        help='Documentar aquí el criterio de identificación de este perfil y su origen '
             '(evidencia de qué formato de documento representa). '
             'No hardcodear reglas de negocio en Python: este modelo es solo el punto '
             'de partida de configuración.'
    )
