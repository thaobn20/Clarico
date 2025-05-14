from odoo import fields, models


class ReportStockPicking(models.Model):
    _inherit = 'stock.picking'

    def get_report_default_today(self):
        return fields.Date.today()
