from odoo import api, fields, models, _

class ZaloZNSTemplate(models.Model):
    _name = 'zalo.zns.template'
    _description = 'Zalo ZNS Template'
    
    name = fields.Char(string='Name', required=True)
    template_id = fields.Char(string='Template ID', required=True)
    template_code = fields.Char(string='Template Code')
    template_content = fields.Text(string='Content')
    template_variation = fields.Text(string='Parameter Variations')
    status = fields.Selection([
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('rejected', 'Rejected')
    ], string='Status', default='active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Add fields to store parameter definitions
    parameter_ids = fields.One2many('zalo.zns.template.parameter', 'template_id', string='Parameters')

class ZaloZNSTemplateParameter(models.Model):
    _name = 'zalo.zns.template.parameter'
    _description = 'Zalo ZNS Template Parameter'
    
    name = fields.Char(string='Parameter Name', required=True)
    type = fields.Selection([
        ('text', 'Text'),
        ('number', 'Number'),
        ('url', 'URL'),
        ('email', 'Email'),
        ('date', 'Date')
    ], string='Parameter Type', required=True)
    required = fields.Boolean(string='Required', default=False)
    description = fields.Char(string='Description')
    template_id = fields.Many2one('zalo.zns.template', string='Template', ondelete='cascade')