# wizard/zns_debug_wizards.py
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json
import logging
import traceback
import requests

_logger = logging.getLogger(__name__)

class ZaloZNSTemplateTestResult(models.TransientModel):
    _name = 'zalo.zns.template.test.result'
    _description = 'Zalo ZNS Template Test Result'
    
    template_id = fields.Many2one('zalo.zns.template', string='Template', required=True)
    test_result = fields.Text(string='Test Result', required=True)
    has_errors = fields.Boolean(string='Has Errors')
    has_warnings = fields.Boolean(string='Has Warnings')
    record_id = fields.Integer(string='Record ID')
    record_model = fields.Char(string='Record Model')
    
    def action_view_record(self):
        """View the test record"""
        self.ensure_one()
        
        if not self.record_model or not self.record_id:
            raise UserError(_('Record information not available'))
            
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.record_model,
            'res_id': self.record_id,
            'view_mode': 'form',
            'target': 'current',
        }
        
    def action_create_test_notification(self):
        """Create a test notification without actually sending it"""
        self.ensure_one()
        
        if not self.record_model or not self.record_id:
            raise UserError(_('Record information not available'))
            
        record = self.env[self.record_model].browse(self.record_id)
        if not record.exists():
            raise UserError(_('Test record no longer exists'))
            
        config = self.env['zalo.zns.config'].search([
            ('company_id', '=', self.template_id.company_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            raise UserError(_('ZNS configuration not found'))
            
        # Set test mode temporarily
        original_test_mode = config.test_mode
        config.test_mode = True
        
        try:
            # Try to send (which will only create a record in test mode)
            if hasattr(record, '_send_zns_notification'):
                result = record._send_zns_notification(self.template_id)
                
                # Restore original test mode
                config.test_mode = original_test_mode
                
                return result
            else:
                # Restore original test mode
                config.test_mode = original_test_mode
                
                raise UserError(_('Record does not support sending notifications'))
        except Exception as e:
            # Restore original test mode
            config.test_mode = original_test_mode
            
            raise UserError(_('Failed to create test notification: %s') % str(e))
            
    def action_send_real_notification(self):
        """Send a real notification after reviewing the test"""
        self.ensure_one()
        
        if self.has_errors:
            raise UserError(_('Cannot send notification with errors. Please fix the errors first.'))
            
        if not self.record_model or not self.record_id:
            raise UserError(_('Record information not available'))
            
        record = self.env[self.record_model].browse(self.record_id)
        if not record.exists():
            raise UserError(_('Test record no longer exists'))
            
        # Make sure test mode is off
        config = self.env['zalo.zns.config'].search([
            ('company_id', '=', self.template_id.company_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            raise UserError(_('ZNS configuration not found'))
            
        original_test_mode = config.test_mode
        config.test_mode = False
        
        try:
            # Send the notification
            if hasattr(record, '_send_zns_notification'):
                result = record._send_zns_notification(self.template_id)
                
                # Restore original test mode
                config.test_mode = original_test_mode
                
                return result
            else:
                # Restore original test mode
                config.test_mode = original_test_mode
                
                raise UserError(_('Record does not support sending notifications'))
        except Exception as e:
            # Restore original test mode
            config.test_mode = original_test_mode
            
            raise UserError(_('Failed to send notification: %s') % str(e))

class ZaloZNSDebugTools(models.TransientModel):
    _name = 'zalo.zns.debug.tools'
    _description = 'Zalo ZNS Debug Tools'
    
    debug_action = fields.Selection([
        ('test_connection', 'Test API Connection'),
        ('clean_logs', 'Clean Debug Logs'),
        ('validate_templates', 'Validate All Templates'),
        ('check_failed', 'Check Failed Notifications'),
    ], string='Debug Action', required=True, default='test_connection')
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    date_from = fields.Date(string='From Date', default=lambda self: fields.Date.context_today(self))
    date_to = fields.Date(string='To Date', default=lambda self: fields.Date.context_today(self))
    
    def action_execute(self):
        """Execute the selected debug action"""
        self.ensure_one()
        
        if self.debug_action == 'test_connection':
            return self._test_connection()
        elif self.debug_action == 'clean_logs':
            return self._clean_logs()
        elif self.debug_action == 'validate_templates':
            return self._validate_templates()
        elif self.debug_action == 'check_failed':
            return self._check_failed()
        else:
            return {'type': 'ir.actions.act_window_close'}
    
    def _test_connection(self):
        """Test API connection with detailed output"""
        config = self.env['zalo.zns.config'].search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            raise UserError(_('ZNS configuration not found for this company'))
        
        # Enable debug mode temporarily
        original_debug_mode = config.debug_mode
        config.debug_mode = True
        
        try:
            # Test the connection
            result = config.test_connection()
            
            # Restore original debug mode
            config.debug_mode = original_debug_mode
            
            return result
        except Exception as e:
            # Restore original debug mode
            config.debug_mode = original_debug_mode
            
            # Create a detailed error log
            error_details = traceback.format_exc()
            self.env['zalo.zns.debug.log'].add_log(
                title="Connection Test Error",
                content=f"Error: {str(e)}\n\n{error_details}",
                level='error',
                model='zalo.zns.config',
                res_id=config.id
            )
            
            # Show the error
            raise UserError(_('Connection test failed: %s\n\nCheck the debug logs for details.') % str(e))
            
    def _clean_logs(self):
        """Clean debug logs older than the retention period"""
        config = self.env['zalo.zns.config'].search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            raise UserError(_('ZNS configuration not found for this company'))
            
        retention_days = config.log_retention_days or 30
        self.env['zalo.zns.debug.log'].auto_clean_logs()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Logs Cleaned'),
                'message': _('Removed debug logs older than %s days') % retention_days,
                'sticky': False,
                'type': 'success',
            }
        }
        
    def _validate_templates(self):
        """Validate all templates for the company"""
        templates = self.env['zalo.zns.template'].search([
            ('company_id', '=', self.company_id.id),
            ('status', '=', 'active')
        ])
        
        if not templates:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Templates'),
                    'message': _('No active templates found for this company'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        valid_count = 0
        invalid_count = 0
        
        for template in templates:
            try:
                # Try to test the template
                template.action_test_template()
                
                # Check for errors in the result
                if template.last_test_result:
                    test_result = json.loads(template.last_test_result)
                    if test_result.get('errors'):
                        invalid_count += 1
                    else:
                        valid_count += 1
                else:
                    invalid_count += 1
            except Exception:
                invalid_count += 1
                continue
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Template Validation Complete'),
                'message': _('%s templates valid, %s templates have issues') % (valid_count, invalid_count),
                'sticky': False,
                'type': 'info',
            }
        }
        
    def _check_failed(self):
        """Check and analyze failed notifications"""
        domain = [
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
            ('status', '=', 'failed'),
            ('company_id', '=', self.company_id.id),
        ]
        
        failed_notifications = self.env['zalo.zns.history'].search(domain)
        
        if not failed_notifications:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Failed Notifications'),
                    'message': _('No failed notifications found in the selected date range'),
                    'sticky': False,
                    'type': 'info',
                }
            }
            
        # Analyze common error patterns
        error_patterns = {}
        
        for notification in failed_notifications:
            error_msg = notification.error_message or 'Unknown error'
            
            # Simplify error message to group similar errors
            simplified_error = error_msg[:100] if error_msg else 'Unknown error'
            
            if simplified_error in error_patterns:
                error_patterns[simplified_error]['count'] += 1
                error_patterns[simplified_error]['ids'].append(notification.id)
            else:
                error_patterns[simplified_error] = {
                    'count': 1,
                    'ids': [notification.id],
                    'full_error': error_msg
                }
                
        # Create a summary log
        summary_content = f"Found {len(failed_notifications)} failed notifications\n\n"
        summary_content += "Error pattern analysis:\n"
        
        for pattern, data in error_patterns.items():
            summary_content += f"- {pattern} ({data['count']} occurrences)\n"
            
        self.env['zalo.zns.debug.log'].add_log(
            title="Failed Notifications Analysis",
            content=summary_content,
            level='info'
        )
        
        # Return action to view failed notifications
        return {
            'name': _('Failed Notifications'),
            'type': 'ir.actions.act_window',
            'res_model': 'zalo.zns.history',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', failed_notifications.ids)],
            'context': {'create': False}
        }