# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import pandas as pd
from io import BytesIO
import logging

_logger = logging.getLogger(__name__)

class LumberConsolidationImportWizard(models.TransientModel):
    _name = 'lumber.consolidation.import.wizard'
    _description = 'Asistente de Importación de Consolidación desde Excel'
    
    shipment_id = fields.Many2one(
        'lumber.export.shipment',
        string='Embarque',
        required=True,
        default=lambda self: self.env.context.get('active_id')
    )
    
    file_data = fields.Binary(
        string='Archivo Excel (LISTADO-TARJAS-MN)',
        required=True,
        help='Subir Excel con formato: Contenedor | Sello | Etiqueta | ...'
    )
    
    file_name = fields.Char('Nombre Archivo')
    
    validate_only = fields.Boolean(
        string='Solo Validar',
        default=False,
        help='Si está marcado, solo valida sin importar'
    )
    
    # Resultados de validación
    validation_summary = fields.Text(
        string='Resumen de Validación',
        readonly=True
    )
    
    validation_state = fields.Selection([
        ('pending', 'Pendiente'),
        ('validated', 'Validado'),
        ('error', 'Con Errores')
    ], default='pending', readonly=True)
    
    def action_validate_file(self):
        """Valida el archivo sin importar"""
        self.validate_only = True
        return self.action_import_consolidation()
    
    def action_import_consolidation(self):
        """Procesa el Excel y asigna lotes a contenedores"""
        self.ensure_one()
        
        if not self.file_data:
            raise UserError(_('Debe subir un archivo Excel'))
        
        try:
            # Decodificar archivo
            file_content = base64.b64decode(self.file_data)
            df = pd.read_excel(BytesIO(file_content), sheet_name=0)
            
            # Detectar estructura del Excel
            container_col = None
            seal_col = None
            label_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if 'contenedor' in col_lower:
                    container_col = col
                elif 'sello' in col_lower:
                    seal_col = col
                elif 'etiqueta' in col_lower or 'lote' in col_lower:
                    label_col = col
            
            if not all([container_col, seal_col, label_col]):
                raise UserError(_(
                    'El Excel debe tener columnas: Contenedor, Sello, Etiqueta/Lote'
                ))
            
            # Procesar datos
            summary = self._process_consolidation_data(
                df, container_col, seal_col, label_col
            )
            
            # Si es solo validación, mostrar resumen
            if self.validate_only:
                self.validation_summary = summary['message']
                self.validation_state = 'validated' if summary['success'] else 'error'
                
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'lumber.consolidation.import.wizard',
                    'res_id': self.id,
                    'view_mode': 'form',
                    'target': 'new',
                }
            
            # Importación real
            if summary['success']:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Consolidación Completada'),
                        'message': summary['message'],
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(summary['message'])
                
        except Exception as e:
            _logger.error(f'Error en importación: {str(e)}', exc_info=True)
            raise UserError(_(
                f'Error al procesar el archivo:\n{str(e)}'
            ))
    
    def _process_consolidation_data(self, df, container_col, seal_col, label_col):
        """Procesa los datos del DataFrame"""
        current_container = None
        container_assignments = {}
        errors = []
        warnings = []
        
        lots_assigned = 0
        containers_created = 0
        
        for idx, row in df.iterrows():
            # Detectar nuevo contenedor
            if pd.notna(row.get(container_col)):
                container_code = str(row[container_col]).strip()
                seal = str(row[seal_col]).strip() if pd.notna(row.get(seal_col)) else ''
                
                # Buscar o crear contenedor
                current_container = self.env['lumber.container'].search([
                    ('shipment_id', '=', self.shipment_id.id),
                    ('container_number', '=', container_code)
                ], limit=1)
                
                if not current_container and not self.validate_only:
                    current_container = self.env['lumber.container'].create({
                        'shipment_id': self.shipment_id.id,
                        'container_number': container_code,
                        'seal_number': seal,
                        'container_type': '40HC'
                    })
                    containers_created += 1
                
                container_assignments[container_code] = []
            
            # Asignar lote al contenedor actual
            if pd.notna(row.get(label_col)) and current_container:
                label = str(int(float(row[label_col])))  # Manejo robusto
                
                # Buscar lote por etiqueta del proveedor
                lot = self.env['stock.lot'].search([
                    ('supplier_label', '=', label)
                ], limit=1)
                
                if not lot:
                    # Intentar buscar por nombre
                    lot = self.env['stock.lot'].search([
                        ('name', 'ilike', label)
                    ], limit=1)
                
                if lot:
                    if not self.validate_only:
                        lot.write({
                            'container_id': current_container.id,
                            'estado_trazabilidad': 'consolidado'
                        })
                    
                    container_assignments[current_container.container_number].append(lot.name)
                    lots_assigned += 1
                else:
                    warnings.append(f'Lote {label} no encontrado en sistema')
        
        # Generar resumen
        message_lines = [
            f'✓ Contenedores procesados: {len(container_assignments)}',
            f'✓ Contenedores creados: {containers_created}',
            f'✓ Lotes asignados: {lots_assigned}',
        ]
        
        if warnings:
            message_lines.append(f'\n⚠ Advertencias: {len(warnings)}')
            message_lines.extend(warnings[:10])  # Primeras 10
        
        if errors:
            message_lines.append(f'\n❌ Errores: {len(errors)}')
            message_lines.extend(errors)
        
        return {
            'success': len(errors) == 0,
            'message': '\n'.join(message_lines),
            'containers': len(container_assignments),
            'lots': lots_assigned
        }
