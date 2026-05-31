# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PurchaseIntake(models.AbstractModel):
    _name = 'madenat.purchase.intake'
    _description = 'Contrato de Intake de Compras (MADENAT)'

    # ------------------------------
    # Utilidades internas (ownership)
    # ------------------------------

    @api.model
    def _get_required_uom_name(self):
        """Nombre visible de la UoM requerida para el maestro (configurable)."""
        return 'm³'

    @api.model
    def _get_master_default_code(self):
        """Código único del producto maestro de madera genérica."""
        return 'MADERA_GENERICA'

    @api.model
    def ensure_master_product(self):
        """Garantiza maestro MADERA_GENERICA con UoM m³ y tracking por lote.
        Regla de Oro: solo Purchasing crea/valida este maestro.
        """
        Product = self.env['product.product']
        Uom = self.env['uom.uom']
        uom_name = self._get_required_uom_name()

        uom_m3 = Uom.search([('name', '=', uom_name)], limit=1)
        if not uom_m3:
            raise UserError(_('No existe la UoM %s; crea/configura la unidad antes de continuar.') % uom_name)

        default_code = self._get_master_default_code()
        prod = Product.search([('default_code', '=', default_code)], limit=1)
        
        if not prod:
            # CREAR producto nuevo con configuración correcta
            prod = Product.create({
                'name': 'MADERA GENERICA',
                'default_code': default_code,
                'type': 'consu',  # ✅ Correcto para tu Odoo 18
                'tracking': 'lot',  # ✅ CRÍTICO: trazabilidad por lote
                'uom_id': uom_m3.id,
                'uom_po_id': uom_m3.id,
            })
            _logger.info("✅ Maestro creado: %s (%s) - Type: %s, Tracking: %s", 
                        prod.display_name, default_code, prod.type, prod.tracking)
        else:
            # VALIDAR y CORREGIR producto existente
            errors = []
            needs_update = {}
            
            # 1. Validar tipo
            if prod.type != 'consu':
                errors.append(f"Tipo incorrecto: '{prod.type}' (debe ser 'consu')")
            
            # 2. Validar tracking ← EL PROBLEMA PRINCIPAL
            if prod.tracking != 'lot':
                # Verificar si tiene movimientos de stock
                moves_count = self.env['stock.move'].search_count([('product_id', '=', prod.id)])
                if moves_count > 0:
                    errors.append(
                        f"Tracking incorrecto: '{prod.tracking}' (debe ser 'lot') "
                        f"pero tiene {moves_count} movimiento(s) de stock"
                    )
                else:
                    needs_update['tracking'] = 'lot'
                    _logger.warning("⚠️ Corrigiendo tracking de %s: none → lot", default_code)
            
            # 3. Validar UoM
            if prod.uom_id != uom_m3:
                moves_count = self.env['stock.move'].search_count([('product_id', '=', prod.id)])
                if moves_count > 0:
                    errors.append(
                        f"UoM incorrecta: '{prod.uom_id.name}' (debe ser '{uom_name}') "
                        f"pero tiene {moves_count} movimiento(s) de stock"
                    )
                else:
                    needs_update['uom_id'] = uom_m3.id
                    needs_update['uom_po_id'] = uom_m3.id
                    _logger.warning("⚠️ Corrigiendo UoM de %s: %s → %s", 
                                default_code, prod.uom_id.name, uom_name)
            
            # 4. Aplicar correcciones si es posible
            if errors:
                error_msg = (
                    f"❌ CONFIGURACIÓN INCORRECTA DEL PRODUCTO MAESTRO '{default_code}':\n\n"
                    + "\n".join(f"  • {e}" for e in errors) +
                    "\n\nSOLUCIÓN:\n"
                    "1. Ir a Inventario → Productos → MADERA_GENERICA\n"
                    "2. Cambiar 'Tipo de Producto' a 'Goods'\n"
                    "3. Activar 'Track Inventory'\n"
                    "4. En 'Tracking' seleccionar 'By Lots'\n"
                    "5. Cambiar 'Unidad de Medida' a 'm³'\n"
                    "6. Guardar y reintentar"
                )
                raise UserError(_(error_msg))
            
            if needs_update:
                prod.write(needs_update)
                _logger.info("✅ Maestro corregido: %s - Cambios: %s", default_code, needs_update)
        
        return prod


    # ------------------------------
    # API principal para Ingestión
    # ------------------------------

    @api.model
    def validate_or_create_po(self, payload, policy=None):
        """Valida/vincula o crea una PO desde un payload normalizado.

        payload:
          - partner_id: int (requerido para cualquier acción)
          - partner_ref: str (requerido si auto_create=False)
          - currency_id: int (opcional)
          - lines: [{'product_id','name','qty','uom_id','price'}]
        policy:
          - auto_create: bool (default False) -> si no hay match, crear PO
          - provisional: bool (default True) -> flag en PO creada

        Retorna: {'status': 'linked'|'created'|'created_provisional'|'pending_link',
                  'po_id': int|None, 'reason': str|None}
        """
        policy = policy or {}
        auto = bool(policy.get('auto_create', False))
        provisional = bool(policy.get('provisional', True))

        partner_id = payload.get('partner_id')
        partner_ref = payload.get('partner_ref')
        currency_id = payload.get('currency_id')
        lines = payload.get('lines') or []

        # Validaciones mínimas
        if not partner_id:
            return {'status': 'pending_link', 'po_id': None, 'reason': 'missing_partner'}
        if not partner_ref and not auto:
            # Sin referencia no se puede vincular; requiere revisión manual
            return {'status': 'pending_link', 'po_id': None, 'reason': 'missing_partner_ref'}

        PO = self.env['purchase.order']

        # 1) Intento de vinculación
        domain = [('partner_id', '=', partner_id)]
        if partner_ref:
            domain.append(('partner_ref', '=', partner_ref))
        po = PO.search(domain, limit=1)
        if po:
            _logger.info("Intake: vinculado a PO %s (partner_ref=%s)", po.name, partner_ref or '')
            return {'status': 'linked', 'po_id': po.id}

        # 2) Política: si no crear automáticamente, pasar a revisión
        if not auto:
            _logger.info("Intake: pendiente de vinculación (auto_create=False)")
            return {'status': 'pending_link', 'po_id': None, 'reason': 'policy_auto_create_off'}

        # 3) Crear PO (ownership Purchasing)
        self.ensure_master_product()

        vals = {
            'partner_id': partner_id,
            'partner_ref': partner_ref or _('OC Provisional'),
            'currency_id': currency_id,
            'provisional': provisional,
            'order_line': [],
        }

        # Normalización defensiva de líneas
        for ln in lines:
            vals['order_line'].append((0, 0, {
                'product_id': ln.get('product_id'),
                'name': (ln.get('name') or '/')[:256],
                'product_qty': float(ln.get('qty') or 0.0),
                'product_uom': ln.get('uom_id'),
                'price_unit': float(ln.get('price') or 0.0),
            }))

        po = PO.create(vals)
        _logger.info("Intake: PO creada %s (provisional=%s)", po.name, provisional)
        return {
            'status': 'created_provisional' if provisional else 'created',
            'po_id': po.id,
            'reason': None
        }
