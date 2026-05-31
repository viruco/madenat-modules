from odoo import models, fields, api

class AccountExpenseMapping(models.Model):
    """
    MODELO: Mapeo de Gastos por Categoría de Proveedor
    ===================================================
    
    Propósito:
    ----------
    Establecer relaciones automáticas entre categorías de proveedores 
    y cuentas contables específicas para facilitar el procesamiento 
    automático de facturas y la correcta clasificación contable.
    
    Funcionalidades Principales:
    ----------------------------
    • Asignación automática de cuentas contables por categoría de proveedor
    • Validación de unicidad por categoría
    • Nombre automático descriptivo
    • Método helper para consulta programática
    
    Flujo de Trabajo:
    -----------------
    1. Configurar mapeo en este modelo
    2. Al crear facturas de proveedores, usar categoría para asignar cuenta
    3. Contabilización automática según mapeo establecido
    
    Notas Técnicas:
    ---------------
    • Campo expense_account_id es opcional inicialmente para evitar errores
    • Restricción de base de datos garantiza una categoría única
    • Método get_account_for_category() para uso en otros modelos
    """
    
    _name = 'account.expense.mapping'
    _description = 'Mapeo de Gastos por Categoría de Proveedor'
    _order = 'vendor_category'
    
    # ======================
    # CAMPOS DEL MODELO
    # ======================
    
    name = fields.Char(
        string='Nombre del Mapeo', 
        compute='_compute_name', 
        store=True,
        help='Nombre automático generado para identificar el mapeo (Categoría - Código Cuenta)'
    )
    
    vendor_category = fields.Selection(
        selection=[
            ('transport', '🚚 Transporte'),
            ('fuel', '⛽ Combustible'),
            ('logistics', '📦 Logística'),
            ('maintenance', '🔧 Mantenimiento'),
            ('services', '💼 Servicios'),
            ('materials', '📎 Materiales'),
            ('other', '📋 Otros Gastos')
        ], 
        string='Categoría del Proveedor', 
        required=True,
        help='Categoría del servicio o producto del proveedor para clasificación contable'
    )
    
    expense_account_id = fields.Many2one(
        'account.account', 
        string='Cuenta de Gastos',
        required=False,  # OPCIONAL: Permitir creación sin cuenta inicialmente
        # DOMAIN CORREGIDO para Odoo 18
        domain="[('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost'])]",
        help='Cuenta contable donde se registrarán automáticamente los gastos de esta categoría'
    )
    
    active = fields.Boolean(
        string='Activo', 
        default=True,
        help='Indica si el mapeo está activo y disponible para uso en el sistema'
    )
    
    # ======================
    # RESTRICCIONES DE BD
    # ======================
    
    _sql_constraints = [
        (
            'vendor_category_uniq', 
            'unique(vendor_category)', 
            '❌ Ya existe un mapeo para esta categoría de proveedor. ¡La categoría debe ser única!'
        ),
    ]
    
    # ======================
    # MÉTODOS COMPUTADOS
    # ======================
    
    @api.depends('vendor_category', 'expense_account_id')
    def _compute_name(self):
        """
        COMPUTA EL NOMBRE AUTOMÁTICO DEL MAPEO
        --------------------------------------
        Formato: 
        - Con cuenta: "[Categoría] - [Código Cuenta]"
        - Sin cuenta: "[Categoría] (Sin Configurar)"
        
        Ejemplos:
        - "🚚 Transporte - 61-01-001"
        - "📦 Logística (Sin Configurar)"
        """
        for record in self:
            if record.vendor_category:
                # Obtener nombre legible de la categoría
                category_name = dict(self._fields['vendor_category'].selection).get(record.vendor_category)
                
                if record.expense_account_id and record.expense_account_id.code:
                    # Formato con cuenta asignada
                    account_code = record.expense_account_id.code
                    record.name = f"{category_name} - {account_code}"
                else:
                    # Formato sin cuenta asignada
                    record.name = f"{category_name} (Sin Configurar)"
            else:
                # Valor por defecto para nuevos registros
                record.name = "Nuevo Mapeo de Gastos"
    
    # ======================
    # MÉTODOS PÚBLICOS
    # ======================
    
    def get_account_for_category(self, category):
        """
        MÉTODO HELPER: Obtener Cuenta Contable por Categoría
        ----------------------------------------------------
        
        Parámetros:
        • category (str): Código de la categoría del proveedor
        
        Retorna:
        • account.account: Objeto de cuenta contable asociada
        • False: Si no existe mapeo activo para la categoría
        
        Uso:
        • Llamado desde otros modelos para asignación automática
        • Validación en procesos de facturación
        """
        if not category:
            return False
            
        mapping = self.search([
            ('vendor_category', '=', category),
            ('active', '=', True),
            ('expense_account_id', '!=', False)
        ], limit=1)
        
        return mapping.expense_account_id if mapping else False
    
    def update_mapping_from_ui(self, category, account_id):
        """
        MÉTODO: Actualizar Mapeo desde Interfaz
        ---------------------------------------
        Para uso en wizards o actualizaciones masivas desde UI
        
        Parámetros:
        • category (str): Categoría a actualizar
        • account_id (int): ID de la cuenta contable
        
        Retorna:
        • bool: True si se actualizó correctamente
        """
        mapping = self.search([('vendor_category', '=', category)], limit=1)
        if mapping:
            mapping.write({'expense_account_id': account_id})
            return True
        return False