from odoo import api, fields, models, _
import json
import requests
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    zns_notification_ids = fields.One2many('zalo.zns.history', 'res_id', 
                                          domain=[('model', '=', 'sale.order')],
                                          string='ZNS Notifications')
    zns_notification_count = fields.Integer(compute='_compute_zns_notification_count')
    partner_phone_normalized = fields.Char(compute='_compute_partner_phone_normalized', store=True)
    
    @api.depends('zns_notification_ids')
    def _compute_zns_notification_count(self):
        for record in self:
            record.zns_notification_count = len(record.zns_notification_ids)
    
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
                    'message': _('Customer has no phone number.'),
                    'sticky': False,
                    'type': 'danger',
                }
            }
        
        # Get available SO templates
        templates = self.env['zalo.zns.template'].search([
            ('is_so_template', '=', True),
            ('status', '=', 'active'),
            ('company_id', '=', self.company_id.id)
        ])
        
        if not templates:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('No active Sales Order ZNS templates found.'),
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
                    'default_model': 'sale.order',
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
    
    debug_mode = config.debug_mode
    test_mode = config.test_mode
    
    if debug_mode:
        _logger.info("=== ZNS DEBUG: Sending notification from %s (ID: %s) ===", 
                     self._name, self.id)
        _logger.info("Template: %s (ID: %s)", template.name, template.id)
        _logger.info("Phone: %s", self.partner_phone_normalized)
            
    # Prepare parameters
    params = {}
    try:
        for param in template.params:
            if param.field_id:
                field_name = param.field_id.name
                
                if debug_mode:
                    _logger.info("Processing parameter %s mapped to field %s", 
                                 param.name, field_name)
                
                if not hasattr(self, field_name):
                    if debug_mode:
                        _logger.warning("Field %s not found on model %s", field_name, self._name)
                    params[param.name] = param.default_value or ''
                    continue
                    
                field_value = self[field_name]
                
                # Handle different field types with debugging
                if param.field_id.ttype == 'many2one':
                    if field_value:
                        field_value = field_value.name
                    else:
                        field_value = ''
                elif param.field_id.ttype == 'date':
                    field_value = field_value.strftime('%d/%m/%Y') if field_value else ''
                elif param.field_id.ttype == 'datetime':
                    field_value = field_value.strftime('%d/%m/%Y %H:%M') if field_value else ''
                elif param.field_id.ttype == 'float':
                    field_value = '{:,.2f}'.format(field_value) if field_value else '0.00'
                    
                params[param.name] = field_value
                
                if debug_mode:
                    _logger.info("Parameter %s value set to: %s", param.name, field_value)
            else:
                params[param.name] = param.default_value or ''
                
                if debug_mode:
                    _logger.info("Parameter %s using default value: %s", 
                                 param.name, param.default_value)
    except Exception as e:
        error_details = traceback.format_exc()
        
        if debug_mode:
            _logger.error("=== ZNS DEBUG: Parameter preparation error ===")
            _logger.error("Exception: %s", str(e))
            _logger.error("Traceback: %s", error_details)
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Error'),
                'message': _('Failed to prepare parameters: %s') % str(e),
                'sticky': False,
                'type': 'danger',
            }
        }
    
    # Create history record
    history_vals = {
        'template_id': template.id,
        'phone': self.partner_phone_normalized,
        'message_content': json.dumps(params),
        'status': 'pending',
        'model': self._name,
        'res_id': self.id,
        'company_id': self.company_id.id,
    }
    
    if debug_mode:
        _logger.info("Creating history record with values: %s", history_vals)
        
    history = self.env['zalo.zns.history'].create(history_vals)
    
    # If test mode, don't actually send the notification
    if test_mode:
        if debug_mode:
            _logger.info("=== ZNS DEBUG: Test mode active, not sending actual notification ===")
            
        # Simulate success in test mode
        history.write({
            'status': 'sent',
            'zns_message_id': f'test-{history.id}'
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test Mode'),
                'message': _('Test notification created successfully (not actually sent).'),
                'sticky': False,
                'type': 'success',
            }
        }
    
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
            
            endpoint = f'{config.api_url.rstrip("/")}/send'
            
            if debug_mode:
                _logger.info("Sending request to: %s", endpoint)
                _logger.info("Headers: %s", pprint.pformat(headers))
                _logger.info("Payload: %s", pprint.pformat(payload))
            
            response = requests.post(
                endpoint,
                headers=headers,
                data=json.dumps(payload)
            )
            
            if debug_mode:
                _logger.info("Response Status: %s", response.status_code)
                _logger.info("Response Headers: %s", pprint.pformat(dict(response.headers)))
                _logger.info("Response Body: %s", response.text)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    message_id = result.get('data', {}).get('message_id')
                    
                    if debug_mode:
                        _logger.info("Notification sent successfully with message ID: %s", message_id)
                        
                    history.write({
                        'status': 'sent',
                        'zns_message_id': message_id
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
                    
                    if debug_mode:
                        _logger.error("API reported failure: %s", error_message)
                        _logger.error("Full response: %s", pprint.pformat(result))
                    
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
                
                if debug_mode:
                    _logger.error("HTTP request failed: %s", error_message)
                
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
        error_details = traceback.format_exc()
        
        if debug_mode:
            _logger.error("=== ZNS DEBUG: Send notification exception ===")
            _logger.error("Exception: %s", str(e))
            _logger.error("Traceback: %s", error_details)
        
        history.write({
            'status': 'failed',
            'error_message': f"{str(e)}\n\n{error_details}"
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