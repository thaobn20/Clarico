from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_domain_service = fields.Boolean('Is Domain Service')
    is_hosting_service = fields.Boolean('Is Hosting Service')
    service_type = fields.Selection([
        ('domain', 'Domain Registration/Renewal'),
        ('hosting_shared', 'Shared Hosting'),
        ('hosting_vps', 'VPS Hosting'),
        ('hosting_dedicated', 'Dedicated Server'),
        ('hosting_cloud', 'Cloud Instance'),
        ('extension', 'Service Extension')
    ], string='Service Type')