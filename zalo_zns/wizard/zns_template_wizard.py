from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ZaloZNSTemplateTest(models.TransientModel):
    _name = 'zalo.zns.template.test'
    _description = 'Test ZNS Template'
    
    template_id = fields.Many2one('zalo.zns.template', string='Template', required=True)
    phone = fields.Char(string='Phone Number', required=True, help='Format: 84xxx')
    parameter_ids = fields.One2many('zalo.zns.template.test.param', 'wizard_id', string='Parameters')
    
    @api.onchange('template_id')
    def _onchange_template_id(self):
        self.parameter_ids = [(5, 0, 0)]
        if self.template_id:
            for param in self.template_id.parameter_ids:
                self.parameter_ids = [(0, 0, {
                    'name': param.name,
                    'param_type': param.type,
                    'required': param.required,
                    'description': param.description,
                })]
    
    def action_send_test(self):
        self.ensure_one()
        
        # Validate phone number
        phone = self.phone
        if not phone:
            raise UserError(_('Please enter a phone number'))
            
        # Format phone if needed
        if phone.startswith('0'):
            phone = '84' + phone[1:]
        elif not phone.startswith('84') and not phone.startswith('+84'):
            phone = '84' + phone
        
        # Collect parameters
        params = {}
        for param in self.parameter_ids:
            if param.required and not param.value:
                raise UserError(_('Parameter "%s" is required') % param.name)
            params[param.name] = param.value
        
        # Get ZNS config
        zns_config = self.env['zalo.zns.config'].search([], limit=1)
        if not zns_config:
            raise UserError(_('No ZNS configuration found'))
        
        # Send test message
        result = zns_config.send_zns_message(phone, self.template_id.template_id, params)
        
        if result.get('success'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Test message sent successfully. Message ID: %s') % result.get('message_id'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to send test message: %s') % result.get('error_message'),
                    'sticky': True,
                    'type': 'danger',
                }
            }

class ZaloZNSTemplateTestParam(models.TransientModel):
    _name = 'zalo.zns.template.test.param'
    _description = 'Test ZNS Template Parameter'
    
    wizard_id = fields.Many2one('zalo.zns.template.test', string='Wizard')
    name = fields.Char(string='Name', required=True, readonly=True)
    param_type = fields.Selection([
        ('text', 'Text'),
        ('number', 'Number'),
        ('url', 'URL'),
        ('email', 'Email'),
        ('date', 'Date')
    ], string='Type', required=True, readonly=True)
    required = fields.Boolean(string='Required', readonly=True)
    description = fields.Char(string='Description', readonly=True)
    value = fields.Char(string='Value')

class ZaloZNSTemplatePreview(models.TransientModel):
    _name = 'zalo.zns.template.preview'
    _description = 'Preview ZNS Template'
    
    template_id = fields.Many2one('zalo.zns.template', string='Template', required=True, readonly=True)
    content_preview = fields.Text(string='Content Preview', readonly=True)
    parameters = fields.Text(string='Parameters Used', readonly=True)