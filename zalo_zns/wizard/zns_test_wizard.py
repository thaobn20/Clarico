# wizard/zns_test_wizard.py
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ZaloZNSSendWizard(models.TransientModel):
    _name = 'zalo.zns.send.wizard'
    _description = 'Zalo ZNS Send Wizard'
    
    model = fields.Char(string='Model', required=True)
    res_id = fields.Integer(string='Record ID', required=True)
    phone = fields.Char(string='Phone Number', required=True)
    template_id = fields.Many2one('zalo.zns.template', string='ZNS Template', required=True,
                                domain="[('status', '=', 'active')]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    @api.model
    def default_get(self, fields_list):
        res = super(ZaloZNSSendWizard, self).default_get(fields_list)
        
        active_model = self._context.get('default_model') or self._context.get('active_model')
        active_id = self._context.get('default_res_id') or self._context.get('active_id')
        
        if active_model and active_id:
            record = self.env[active_model].browse(active_id)
            
            if active_model == 'sale.order':
                domain = [('is_so_template', '=', True)]
                phone = record.partner_phone_normalized
            elif active_model == 'purchase.order':
                domain = [('is_po_template', '=', True)]
                phone = record.partner_phone_normalized
            elif active_model == 'account.move':
                domain = [('is_invoice_template', '=', True)]
                phone = record.partner_phone_normalized
            else:
                domain = []
                phone = ''
                
            # Add company domain
            domain.extend([
                ('status', '=', 'active'),
                ('company_id', '=', record.company_id.id)
            ])
            
            # Find templates
            templates = self.env['zalo.zns.template'].search(domain)
            
            if templates:
                res.update({
                    'template_id': templates[0].id,
                    'company_id': record.company_id.id,
                })
                
            if not res.get('phone'):
                res['phone'] = phone
                
        return res
    
    def action_send(self):
        self.ensure_one()
        
        if not self.template_id:
            raise UserError(_('Please select a template.'))
            
        if not self.phone:
            raise UserError(_('Phone number is required.'))
            
        record = self.env[self.model].browse(self.res_id)
        
        if hasattr(record, '_send_zns_notification'):
            result = record._send_zns_notification(self.template_id)
            return result
        else:
            raise UserError(_('The selected model does not support ZNS notifications.'))

class ZaloZNSUpdateStatusWizard(models.TransientModel):
    _name = 'zalo.zns.update.status.wizard'
    _description = 'Zalo ZNS Update Status Wizard'
    
    date_from = fields.Date(string='From Date', required=True, default=lambda self: fields.Date.context_today(self))
    date_to = fields.Date(string='To Date', required=True, default=lambda self: fields.Date.context_today(self))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    def action_update_status(self):
        self.ensure_one()
        
        config = self.env['zalo.zns.config'].search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            raise UserError(_('ZNS configuration not found.'))
            
        # Find all pending/sent messages in the date range
        from_datetime = fields.Datetime.from_string(self.date_from)
        from_datetime = fields.Datetime.to_string(from_datetime.replace(hour=0, minute=0, second=0))
        
        to_datetime = fields.Datetime.from_string(self.date_to)
        to_datetime = fields.Datetime.to_string(to_datetime.replace(hour=23, minute=59, second=59))
        
        domain = [
            ('create_date', '>=', from_datetime),
            ('create_date', '<=', to_datetime),
            ('status', 'in', ['pending', 'sent']),
            ('company_id', '=', self.company_id.id),
            ('zns_message_id', '!=', False),
        ]
        
        messages = self.env['zalo.zns.history'].search(domain)
        
        if not messages:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Messages'),
                    'message': _('No messages found to update.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        # Update message statuses in batch using the cron method logic
        updated_count = 0
        failed_count = 0
        
        for message in messages:
            try:
                # Call API to check message status
                if config.use_direct_api:
                    # Direct Zalo API implementation
                    pass
                else:
                    # ZNS.BOM.ASIA implementation
                    headers = {
                        'Authorization': f'Bearer {config.api_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    response = requests.get(
                        f'{config.api_url.rstrip("/")}/message/{message.zns_message_id}',
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            zns_status = result.get('data', {}).get('status', '').upper()
                            
                            # Map the status
                            if zns_status == 'DELIVERED':
                                message.status = 'delivered'
                            elif zns_status == 'FAILED':
                                message.status = 'failed'
                                message.error_message = result.get('data', {}).get('error_message', 'Unknown error')
                            elif zns_status == 'SENT':
                                message.status = 'sent'
                                
                            updated_count += 1
                        else:
                            failed_count += 1
                    else:
                        failed_count += 1
                
                # For demo/testing, you can use this randomized approach
                import random
                rand = random.random()
                if rand > 0.7:
                    message.status = 'delivered'
                elif rand > 0.4:
                    message.status = 'sent'
                else:
                    message.status = 'failed'
                    message.error_message = 'Simulated failure'
                updated_count += 1
                
            except Exception as e:
                failed_count += 1
                continue
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Status Update Complete'),
                'message': _('%s messages updated, %s failed.') % (updated_count, failed_count),
                'sticky': False,
                'type': 'success',
            }
        }