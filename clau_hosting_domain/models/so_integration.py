from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    domain_count = fields.Integer(compute='_compute_service_count')
    hosting_count = fields.Integer(compute='_compute_service_count')
    
    @api.depends('order_line.product_id')
    def _compute_service_count(self):
        for order in self:
            order.domain_count = self.env['domain.service'].search_count([('sale_order_id', '=', order.id)])
            order.hosting_count = self.env['hosting.service'].search_count([('sale_order_id', '=', order.id)])
    
    def action_view_domains(self):
        """View domains linked to this SO"""
        self.ensure_one()
        domains = self.env['domain.service'].search([('sale_order_id', '=', self.id)])
        action = self.env.ref('clau_hosting_domain.action_domain_service').read()[0]
        
        if len(domains) > 1:
            action['domain'] = [('id', 'in', domains.ids)]
        elif domains:
            action['views'] = [(self.env.ref('clau_hosting_domain.view_domain_service_form').id, 'form')]
            action['res_id'] = domains.id
        
        return action
    
    def action_view_hosting(self):
        """View hosting services linked to this SO"""
        self.ensure_one()
        hosting = self.env['hosting.service'].search([('sale_order_id', '=', self.id)])
        action = self.env.ref('clau_hosting_domain.action_hosting_service').read()[0]
        
        if len(hosting) > 1:
            action['domain'] = [('id', 'in', hosting.ids)]
        elif hosting:
            action['views'] = [(self.env.ref('clau_hosting_domain.view_hosting_service_form').id, 'form')]
            action['res_id'] = hosting.id
        
        return action