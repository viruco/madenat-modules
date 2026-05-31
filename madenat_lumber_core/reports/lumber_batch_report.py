from odoo import models, fields, api
from odoo.tools import format_date

class LumberBatchReport(models.AbstractModel):
    _name = 'report.madenat_lumber_core.lumber_batch_report'
    _description = 'Reporte de Tarjas por Lote'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.lot'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'stock.lot',
            'docs': docs,
            'format_date': format_date,
            'company': self.env.company,
        }