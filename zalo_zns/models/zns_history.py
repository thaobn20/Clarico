from odoo import api, fields, models

class ZaloZNSHistory(models.Model):
    _name = 'zalo.zns.history'
    _description = 'Zalo ZNS Notification History'
    _order = 'create_date desc'
    
    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    template_id = fields.Many2one('zalo.zns.template', string='Template Used')
    phone = fields.Char(string='Phone Number')
    message_content = fields.Text(string='Message Content')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed')
    ], string='Status', default='pending')
    error_message = fields.Text(string='Error Message')
    model = fields.Char(string='Model')
    res_id = fields.Integer(string='Record ID')
    zns_message_id = fields.Char(string='ZNS Message ID')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Sent By', default=lambda self: self.env.user)
    
    @api.depends('template_id', 'create_date', 'phone')
    def _compute_name(self):
        for record in self:
            if record.create_date:
                date_str = fields.Datetime.from_string(record.create_date).strftime('%Y-%m-%d %H:%M')
                record.name = f"{record.template_id.name or 'ZNS'} - {date_str} - {record.phone or ''}"
            else:
                record.name = f"{record.template_id.name or 'ZNS'} - {record.phone or ''}"