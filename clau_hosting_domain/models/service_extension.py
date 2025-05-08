from odoo import api, fields, models
from datetime import date

class ServiceExtension(models.Model):
    _name = 'service.extension'
    _description = 'Service Add-ons'
    _rec_name = 'name'  # Removed the asterisks
    
    name = fields.Char('Extension Name', required=True)
    price = fields.Float('Cost')
    description = fields.Text('Description')
    
    # Dashboard reference
    dashboard_ids = fields.Many2many(
        'so.service.dashboard',
        'so_dashboard_extension_rel',
        'extension_id',
        'dashboard_id',
        string='Dashboards'
    )
    
    # For backwards compatibility with views that might be using dashboard_id
    dashboard_id = fields.Many2one('so.service.dashboard', string='Primary Dashboard', compute='_compute_dashboard_id', store=False)
    
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
    
    @api.depends('dashboard_ids')
    def _compute_dashboard_id(self):
        """Compute a single dashboard_id for compatibility"""
        for rec in self:
            rec.dashboard_id = rec.dashboard_ids[0].id if rec.dashboard_ids else False
    
    @api.depends('service_id')
    def _compute_service_type(self):  # Removed the asterisks
        """Compute the service type based on the service_id reference"""
        for rec in self:
            if rec.service_id:
                rec.service_type = rec.service_id._name
            else:
                rec.service_type = False
    
    @api.depends('end_date')
    def _compute_days_to_expire(self):  # Removed the asterisks
        """Compute days until expiration"""
        today = date.today()
        for rec in self:
            if rec.end_date:
                delta = (rec.end_date - today).days
                rec.days_to_expire = delta if delta >= 0 else 0
            else:
                rec.days_to_expire = 0
    
    @api.depends('end_date')
    def _compute_status(self):  # Removed the asterisks
        """Compute extension status based on expiration date"""
        today = date.today()
        for rec in self:
            if rec.end_date and rec.end_date < today:
                rec.status = 'expired'
            else:
                rec.status = 'active'
                
    @api.onchange('service_id')
    def _onchange_service_id(self):  # Removed the asterisks
        """When the service changes, try to find its dashboard"""
        if self.service_id:
            # For domain services
            if self.service_type == 'domain.service':
                dashboards = self.env['so.service.dashboard'].search([
                    ('domain_ids', 'in', self.service_id.id)
                ], limit=1)
                if dashboards:
                    # Add the dashboard to the many2many field
                    self.dashboard_ids = [(4, dashboards.id)]
            # For hosting services
            elif self.service_type == 'hosting.service':
                dashboards = self.env['so.service.dashboard'].search([
                    ('hosting_ids', 'in', self.service_id.id)
                ], limit=1)
                if dashboards:
                    # Add the dashboard to the many2many field
                    self.dashboard_ids = [(4, dashboards.id)]