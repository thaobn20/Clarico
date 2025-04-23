from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class BNTSaleReport(models.Model):
    _inherit = 'sale.order'

    valid_until_date = fields.Datetime(string='Valid Until', compute='_compute_valid_until_date', store=True)

    @api.depends('create_date')
    def _compute_valid_until_date(self):
        for record in self:
            if record.create_date:
                record.valid_until_date = record.create_date + relativedelta(days=30)
            else:
                record.valid_until_date = False
