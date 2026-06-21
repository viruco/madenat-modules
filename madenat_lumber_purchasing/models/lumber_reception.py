# -*- coding: utf-8 -*-
"""
Extensión de lumber.reception para integración con compras - Odoo 18 CE
PATCH 2026-06-18: ELIMINADA autocreación de purchase.order.
Convertido a find-and-link con trazabilidad documental de OC.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class LumberReceptionPurchasing(models.Model):
    _inherit = 'lumber.reception'
    
    def _find_po_and_supplier(self, dg_data):
        """
        SOBRESCRITURA PATCH 2026-06-18: find-and-link SIN autocreación.
        
        Busca OC existente por nombre normalizado. Si no encuentra:
        - Persiste oc_reference_raw con la referencia documental detectada
        - NO crea purchase.order automáticamente
        - Deja purchase_id=False, oc_match_status='not_found'
        - Retorna (False, supplier) para que el flujo continúe con referencia manual
        
        Si encuentra match único:
        - Vincula purchase_id = po.id
        - Conserva oc_reference_raw (NUNCA se sobrescribe)
        - oc_match_status = 'singlematch'
        """
        # Validación robusta: manejar None de forma segura
        supplier_rut = dg_data.get('supplier_rut')
        po_ref = dg_data.get('po_ref')
        
        # Convertir None a string vacío antes de .strip()
        supplier_rut = supplier_rut.strip() if supplier_rut else ''
        po_ref = po_ref.strip() if po_ref else ''
        
        _logger.info(f"🔍 [PATCH 2026-06-18] Buscando OC: {po_ref}, Proveedor: {supplier_rut}")
        
        if not po_ref:
            raise UserError(_("No se detectó referencia de OC en el documento PDF."))
        if not supplier_rut:
            raise UserError(_("No se detectó RUT del proveedor en el documento PDF."))
        
        # Buscar Proveedor
        supplier = self.env['res.partner'].search([('vat', '=', supplier_rut)], limit=1)
        if not supplier:
            supplier = self._create_supplier_from_guide(dg_data, supplier_rut)
            self._add_log(f"✅ Proveedor '{supplier.name}' creado automáticamente")
        
        # ═══════════════════════════════════════════════════════════════
        # 🏷️ PERSISTIR REFERENCIA DOCUMENTAL (NUNCA sobrescribir)
        # ═══════════════════════════════════════════════════════════════
        if po_ref and not self.oc_reference_raw:
            self.write({'oc_reference_raw': po_ref})
            _logger.info(
                f"🏷️ oc_reference_raw persistido en lumber.reception: {po_ref} "
                f"para Recepción {self.name}"
            )
        
        # ═══════════════════════════════════════════════════════════════
        # BUSCAR OC EXISTENTE (find-and-link, NO find-or-create)
        # ═══════════════════════════════════════════════════════════════
        # Usar normalize_oc_ref del core para matching robusto
        normalized_ref = self._normalize_oc_ref(po_ref) if hasattr(self, '_normalize_oc_ref') else po_ref.upper().replace(' ', '')
        
        candidates = self.env['purchase.order'].search([
            ('partner_id', '=', supplier.id),
            ('state', 'in', ['draft', 'sent', 'purchase', 'done'])
        ])
        
        # Match por nombre normalizado
        po = candidates.filtered(
            lambda p: (hasattr(self, '_normalize_oc_ref') and self._normalize_oc_ref(p.name or '') == normalized_ref)
                      or (p.name or '').upper().replace(' ', '') == normalized_ref
        )[:1]
        
        # ═══════════════════════════════════════════════════════════════
        # SI EXISTE MATCH ÚNICO - Vincular
        # ═══════════════════════════════════════════════════════════════
        if po:
            self.write({
                'purchase_id': po.id,
                'supplier_id': supplier.id,
                'oc_match_status': 'singlematch',
                'oc_match_note': f'Auto-match por nombre contra PO {po.name}',
                'manual_po_name': False,
            })
            self._add_log(f"✅ OC {po.name} vinculada exitosamente (singlematch).")
            _logger.info(
                f"✅ [PATCH 2026-06-18] OC {po.name} vinculada a Recepción {self.name}. "
                f"oc_reference_raw={self.oc_reference_raw}"
            )
            return po, supplier
        
        # ═══════════════════════════════════════════════════════════════
        # SI NO EXISTE - NO CREAR. Dejar para resolución humana.
        # ═══════════════════════════════════════════════════════════════
        else:
            self.write({
                'purchase_id': False,
                'supplier_id': supplier.id,
                'oc_match_status': 'not_found',
                'oc_match_note': (
                    f'OC {po_ref} no encontrada. Vincular manualmente o crear con supervisión.'
                ),
                'manual_po_name': po_ref,  # Legacy: mantener compatibilidad con vistas existentes
            })
            _logger.warning(
                f"⚠️ [PATCH 2026-06-18] OC '{po_ref}' no encontrada para proveedor {supplier.name}. "
                f"NO se crea automáticamente. Recepción {self.name} queda en modo referencia manual. "
                f"oc_reference_raw={self.oc_reference_raw}"
            )
            self._add_log(
                f"⚠️ OC '{po_ref}' no encontrada. Vincule manualmente o cree la OC con supervisión."
            )
            return False, supplier
    
    def _create_supplier_from_guide(self, dg_data, supplier_rut):
        """Crear proveedor basado en datos de la guía"""
        supplier_name = dg_data.get('supplier_name', f'Proveedor {supplier_rut}')
        
        return self.env['res.partner'].create({
            'name': supplier_name,
            'vat': supplier_rut,
            'supplier_rank': 1,
            'company_type': 'company',
        })
    
    def _create_po_from_guide(self, dg_data, po_ref, supplier):
        """
        ⚠️ DEPRECATED por PATCH 2026-06-18.
        
        Este método se conserva para compatibilidad con código que pueda
        referenciarlo, pero ya NO se invoca desde _find_po_and_supplier.
        
        Si se invoca manualmente, crea una OC con advertencia explícita
        de que la creación automática está deshabilitada por política.
        """
        _logger.warning(
            f"⚠️ _create_po_from_guide llamado manualmente para OC '{po_ref}'. "
            f"La autocreación de OC está DESHABILITADA por PATCH 2026-06-18. "
            f"Se creará la OC pero con marca de 'revisión requerida'."
        )
        # Buscar producto genérico para madera
        lumber_product = self.env['product.product'].search([
            ('default_code', '=', 'MADERA_GENERICA')
        ], limit=1)

        if not lumber_product or not lumber_product.active:
            raise UserError("Falta producto base MADERA_GENERICA en la base o está inactivo. Reinstale/actualice el módulo para crear el dato maestro por XML.")
        if lumber_product.type != 'product' or lumber_product.uom_id != self.env.ref('uom.product_uom_cubic_meter'):
            raise UserError("El producto 'MADERA_GENERICA' está mal configurado. Debe ser tipo 'Almacenable' y unidad en m³. Corrija manualmente vía inventario Odoo o recargue el XML.")
        
        # Extraer datos específicos de madera
        net_total = dg_data.get('net_total', 0)
        total_volume = dg_data.get('total_volume', 1)
        unit_price = net_total / total_volume if total_volume > 0 else 0
        
        # Crear OC CON CAMPOS ESPECÍFICOS DE MADERA
        po_vals = {
            'name': po_ref,
            'partner_id': supplier.id,
            'date_order': fields.Datetime.now(),
            # Campos extendidos de madera (si existen en tu modelo)
            'lumber_quality': 'col_a',
            'wood_type': 'pine',
            'treatment': 'kiln_dried',
            'thickness_mm': 45.0,
            'order_line': [(0, 0, {
                'product_id': lumber_product.id,
                'product_qty': total_volume,
                'price_unit': round(unit_price, 2),
                'name': f'Madera de Pino Radiata - {total_volume:.2f} m³',
                'product_uom': self.env.ref('uom.product_uom_unit').id,
            })],
        }
        
        po = self.env['purchase.order'].create(po_vals)
        # NO confirmar automáticamente — requiere revisión humana
        # po.button_confirm()
        
        return po
    
    def open_related_po(self):
        """Abrir la OC relacionada desde la recepción"""
        self.ensure_one()
        if not self.purchase_order:
            raise UserError(_("No hay Orden de Compra asociada."))
            
        po = self.env['purchase.order'].search([('name', '=', self.purchase_order)], limit=1)
        if not po:
            raise UserError(_("Orden de Compra no encontrada."))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': po.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_test_processing(self):
        """Método de prueba para diagnosticar el problema"""
        self.ensure_one()
        self._add_log("🧪 INICIANDO PRUEBA DE DIAGNÓSTICO...")
        
        try:
            # Probar solo el parsing del Excel
            self._add_log("📊 Probando análisis de Excel...")
            pl_data = self._parse_packing_list()
            self._add_log(f"✅ Excel analizado: {len(pl_data.get('lines', []))} líneas")
            
            # Probar solo el parsing del PDF
            self._add_log("📄 Probando análisis de PDF...")
            dg_data = self._parse_dispatch_guide()
            self._add_log(f"✅ PDF analizado: {dg_data}")
            
            self._add_log("🎉 PRUEBA EXITOSA - Todos los componentes funcionan")
            
        except Exception as e:
            self._add_log(f"❌ ERROR EN PRUEBA: {str(e)}")
            self._add_log("💡 Posible solución: Verificar formato de archivos")
            raise