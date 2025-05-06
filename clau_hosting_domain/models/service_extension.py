from odoo import api, fields, models
from datetime import date

class ServiceExtension(models.Model):
    _name = 'service.extension'
    _description = 'Service Add-ons'
    _rec_name = 'name'

    name = fields.Char('Extension Name', required=True)
    price = fields.Float('Cost')
    description = fields.Text('Description')
    
    service_type = fields.Selection([
        ('domain.service', 'Domain'),
        ('hosting.service', 'Hosting')
    ], string='Service Type', compute='_compute_service_type', store=True)
    
    service_id = fields.Reference(
        selection=[
            ('domain.service', 'Domain'),
            ('hosting.service', 'Hosting')
        ], 
        string='Linked Service',
        required=True)
        
    start_date = fields.Date('Start Date', default=fields.Date.today)
    end_date = fields.Date('End Date')
    days_to_expire = fields.Integer('Days to Expire', compute='_compute_days_to_expire', store=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired')
    ], string='Status', compute='_compute_status', store=True)
    active = fields.Boolean(default=True)
    
    @api.depends('service_id')
    def _compute_service_type(self):
        """Compute the service type based on the service_id reference"""
        for rec in self:
            if rec.service_id:
                rec.service_type = rec.service_id._name
            else:
                rec.service_type = False
    
    @api.depends('end_date')
    def _compute_days_to_expire(self):
        """Compute days until expiration"""
        today = date.today()
        for rec in self:
            if rec.end_date:
                delta = (rec.end_date - today).days
                rec.days_to_expire = delta if delta >= 0 else 0
            else:
                rec.days_to_expire = 0
    
    @api.depends('end_date')
    def _compute_status(self):
        """Compute extension status based on expiration date"""
        today = date.today()
        for rec in self:
            if rec.end_date and rec.end_date < today:
                rec.status = 'expired'
            else:
                rec.status = 'active'