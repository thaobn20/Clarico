from odoo import api, fields, models
from datetime import timedelta

class ServiceCommonMixin(models.AbstractModel):
    _name = 'service.common.mixin'
    _description = 'Shared fields for domain and hosting services'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # SO Integration fields
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', tracking=True)
    sale_line_id = fields.Many2one('sale.order.line', string='Sales Order Line', tracking=True)
    
    # Add this computed field to calculate total extension costs
    extension_total = fields.Float(
        string='Total Add-ons Cost',
        compute='_compute_extension_total',
        store=True
    )
    
    # Add a computed field for total service value
    service_value = fields.Float(
        string='Service Value',
        compute='_compute_service_value',
        store=True
    )
    
    name = fields.Char('Service / Domain Name', required=True, tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    start_date = fields.Date('Start Date', default=fields.Date.today, tracking=True)
    end_date = fields.Date('End Date', tracking=True)
    auto_renew = fields.Boolean('Auto Renew', default=True, tracking=True)   
    extension_ids = fields.One2many('service.extension', 'service_id', string='Add-ons')
    service_id_ref = fields.Char(compute='_compute_service_id_ref', store=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended')
    ], string='Status', compute='_compute_status', store=True, tracking=True)
    days_to_expire = fields.Integer('Days to Expire', compute='_compute_days_to_expire', store=True)
    note = fields.Text('Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
    
    @api.depends()
    def _compute_service_id_ref(self):
        """Compute a proper reference string for this record"""
        for rec in self:
            rec.service_id_ref = f"{rec._name},{rec.id}" if rec.id else False
    
    @api.depends('end_date')
    def _compute_status(self):
        today = fields.Date.today()
        for rec in self:
            if not rec.end_date:
                rec.status = 'active'
            elif rec.end_date < today:
                rec.status = 'expired'
            else:
                rec.status = 'active'
    
    @api.depends('end_date')
    def _compute_days_to_expire(self):
        today = fields.Date.today()
        for rec in self:
            if rec.end_date:
                delta = (rec.end_date - today).days
                rec.days_to_expire = delta if delta >= 0 else 0
            else:
                rec.days_to_expire = 0
    
    @api.depends('extension_ids', 'extension_ids.price')
    def _compute_extension_total(self):
        """Calculate the total cost of all extensions"""
        for record in self:
            record.extension_total = sum(record.extension_ids.mapped('price'))
    
    @api.depends('sale_line_id.price_subtotal', 'extension_total')
    def _compute_service_value(self):
        """Calculate the total value of the service including extensions"""
        for record in self:
            base_value = record.sale_line_id.price_subtotal if record.sale_line_id else 0.0
            record.service_value = base_value + record.extension_total
    
    def action_suspend(self):
        self.write({'status': 'suspended'})
    
    def action_reactivate(self):
        self.write({'status': 'active'})
    
    def get_expiring_services(self, days=30):
        """Find services expiring in the next x days"""
        today = fields.Date.today()
        limit_date = today + timedelta(days=days)
        return self.search([
            ('end_date', '>=', today),
            ('end_date', '<=', limit_date),
            ('status', '=', 'active')
        ])
    
    def action_view_sale_order(self):
        """View the linked sales order"""
        self.ensure_one()
        if not self.sale_order_id:
            return {'type': 'ir.actions.act_window_close'}
           
        return {
            'name': 'Sales Order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }