# models/stock_picking.py
from odoo import models, api, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    def _get_report_base_filename(self):
        """Override to change the default filename of the delivery slip"""
        self.ensure_one()
        return 'Delivery Slip - %s' % (self.name)
    
    def print_custom_delivery_slip(self):
        """Add a new method to print a custom delivery slip"""
        return self.env.ref('bom_custom_report.action_custom_delivery_report').report_action(self)