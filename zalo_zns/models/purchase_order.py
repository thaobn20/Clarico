# models/purchase_order.py
from odoo import api, fields, models, _
import json
import requests
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    zns_notification_ids = fields.One2many('zalo.zns.history', 'res_id', 
                                          domain=[('model', '=', 'purchase.order')],
                                          string='ZNS Notifications')
    zns_notification_count = fields.Integer(compute='_compute_zns_notification_count')
    has_zns_notifications = fields.Boolean(string='Has ZNS Notifications', 
                                          compute='_compute_zns_notification_count', 
                                          store=True)  # This field will be searchable
    partner_phone_normalized = fields.Char(compute='_compute_partner_phone_normalized', store=True)
    
    @api.depends('zns_notification_ids')
    def _compute_zns_notification_count(self):
        for record in self:
            record.zns_notification_count = len(record.zns_notification_ids)
            record.has_zns_notifications = bool(record.zns_notification_ids)
    
    @api.depends('partner_id.phone', 'partner_id.mobile')
    def _compute_partner_phone_normalized(self):
        for record in self:
            phone = record.partner_id.mobile or record.partner_id.phone or ''
            # Simple normalization - remove spaces and ensure starts with country code
            phone = phone.replace(' ', '')
            if phone and not phone.startswith('+'):
                # Assuming Vietnam phone numbers - add +84 and remove leading 0 if present
                if phone.startswith('0'):
                    phone = '+84' + phone[1:]
                else:
                    phone = '+84' + phone
            record.partner_phone_normalized = phone
    
    def action_send_zns(self):
        self.ensure_one()
        
        if not self.partner_phone_normalized:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Vendor has no phone number.'),
                    'sticky': False,
                    'type': 'danger',
                }
            }
        
        # Get available PO templates
        templates = self.env['zalo.zns.template'].search([
            ('is_po_template', '=', True),
            ('status', '=', 'active'),
            ('company_id', '=', self.company_id.id)
        ])
        
        if not templates:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('No active Purchase Order ZNS templates found.'),
                    'sticky': False,
                    'type': 'danger',
                }
            }
        
        # If only one template, use it directly; otherwise, open wizard
        if len(templates) == 1:
            return self._send_zns_notification(templates[0])
        else:
            return {
                'name': _('Send ZNS Notification'),
                'type': 'ir.actions.act_window',
                'res_model': 'zalo.zns.send.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_model': 'purchase.order',
                    'default_res_id': self.id,
                    'default_phone': self.partner_phone_normalized,
                },
            }
    
    def _send_zns_notification(self, template):
        self.ensure_one()
        
        config = self.env['zalo.zns.config'].search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('ZNS configuration not found.'),
                    'sticky': False,
                    'type': 'danger',
                }
            }
            
        # Prepare parameters
        params = {}
        for param in template.params:
            if param.field_id:
                field_name = param.field_id.name
                field_value = self[field_name]
                
                # Handle different field types
                if param.field_id.ttype == 'many2one':
                    field_value = field_value.name
                elif param.field_id.ttype == 'date':
                    field_value = field_value.strftime('%d/%m/%Y') if field_value else ''
                elif param.field_id.ttype == 'datetime':
                    field_value = field_value.strftime('%d/%m/%Y %H:%M') if field_value else ''
                elif param.field_id.ttype == 'float':
                    field_value = '{:,.2f}'.format(field_value)
                    
                params[param.name] = field_value
            else:
                params[param.name] = param.default_value or ''
        
        # Create history record
        history_vals = {
            'template_id': template.id,
            'phone': self.partner_phone_normalized,
            'message_content': json.dumps(params),
            'status': 'pending',
            'model': 'purchase.order',
            'res_id': self.id,
            'company_id': self.company_id.id,
        }
        
        history = self.env['zalo.zns.history'].create(history_vals)
        
        # Send notification
        try:
            if config.use_direct_api:
                # Direct Zalo API implementation
                pass
            else:
                # ZNS.BOM.ASIA implementation
                headers = {
                    'Authorization': f'Bearer {config.api_key}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'phone': self.partner_phone_normalized,
                    'template_id': template.template_id,
                    'template_data': params
                }
                
                response = requests.post(
                    f'{config.api_url.rstrip("/")}/send',
                    headers=headers,
                    data=json.dumps(payload)
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        history.write({
                            'status': 'sent',
                            'zns_message_id': result.get('data', {}).get('message_id')
                        })
                        
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('Success'),
                                'message': _('ZNS notification sent successfully.'),
                                'sticky': False,
                                'type': 'success',
                            }
                        }
                    else:
                        error_message = result.get('message', 'Unknown error')
                        history.write({
                            'status': 'failed',
                            'error_message': error_message
                        })
                        
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('Error'),
                                'message': _('Failed to send ZNS: %s') % error_message,
                                'sticky': False,
                                'type': 'danger',
                            }
                        }
                else:
                    error_message = f"Status code: {response.status_code}, Response: {response.text}"
                    history.write({
                        'status': 'failed',
                        'error_message': error_message
                    })
                    
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Error'),
                            'message': _('Failed to send ZNS. %s') % error_message,
                            'sticky': False,
                            'type': 'danger',
                        }
                    }
                    
        except Exception as e:
            _logger.error("ZNS send error: %s", str(e))
            history.write({
                'status': 'failed',
                'error_message': str(e)
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to send ZNS: %s') % str(e),
                    'sticky': False,
                    'type': 'danger',
                }
            }