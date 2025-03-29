# models/zns_debug.py
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json
import logging
import traceback
from datetime import timedelta

_logger = logging.getLogger(__name__)

class ZaloZNSDebugLog(models.Model):
    _name = 'zalo.zns.debug.log'
    _description = 'Zalo ZNS Debug Log'
    _order = 'create_date desc'
    
    name = fields.Char(string='Title', required=True)
    log_level = fields.Selection([
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ], string='Level', required=True, default='info')
    log_content = fields.Text(string='Log Content', required=True)
    request_data = fields.Text(string='Request Data')
    response_data = fields.Text(string='Response Data')
    model = fields.Char(string='Model')
    res_id = fields.Integer(string='Record ID')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    
    @api.model
    def add_log(self, title, content, level='info', model=False, res_id=False, request_data=False, response_data=False):
        """Add a debug log entry"""
        
        # Check if we should store this log based on configuration
        config = self.env['zalo.zns.config'].search([
            ('company_id', '=', self.env.company.id),
            ('active', '=', True)
        ], limit=1)
        
        if not config or not config.debug_mode:
            # Only log in the database if debug mode is enabled
            return False
            
        # Create the log
        try:
            vals = {
                'name': title[:100],  # Truncate to avoid field size issues
                'log_level': level,
                'log_content': content,
                'model': model,
                'res_id': res_id,
            }
            
            if request_data:
                if isinstance(request_data, dict):
                    vals['request_data'] = json.dumps(request_data, indent=2)
                else:
                    vals['request_data'] = str(request_data)
                    
            if response_data:
                if isinstance(response_data, dict):
                    vals['response_data'] = json.dumps(response_data, indent=2)
                else:
                    vals['response_data'] = str(response_data)
                    
            return self.create(vals)
        except Exception as e:
            _logger.error("Failed to create ZNS debug log: %s", str(e))
            return False
            
    @api.model
    def auto_clean_logs(self):
        """Automatically clean old debug logs based on retention policy"""
        config = self.env['zalo.zns.config'].search([
            ('company_id', '=', self.env.company.id),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            return False
            
        retention_days = config.log_retention_days or 30
        cutoff_date = fields.Datetime.now() - timedelta(days=retention_days)
        
        old_logs = self.search([
            ('create_date', '<', cutoff_date)
        ])
        
        if old_logs:
            old_logs.unlink()
            _logger.info("Deleted %s old ZNS debug logs (retention: %s days)", 
                        len(old_logs), retention_days)
            
        return True


class ZaloZNSConfigExtension(models.Model):
    _inherit = 'zalo.zns.config'
    
    # Add debug fields
    debug_mode = fields.Boolean(string='Debug Mode', default=False,
                               help='Enable detailed logging for troubleshooting')
    test_mode = fields.Boolean(string='Test Mode', default=False,
                              help='Use test endpoint and avoid sending real notifications')
    log_retention_days = fields.Integer(string='Log Retention (Days)', default=30,
                                       help='Number of days to keep detailed logs')
    
    def clear_old_logs(self):
        """Manual method to clear old logs"""
        self.ensure_one()
        self.env['zalo.zns.debug.log'].auto_clean_logs()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Logs Cleaned'),
                'message': _('Old debug logs have been cleared based on retention policy.'),
                'sticky': False,
                'type': 'success',
            }
        }


class ZaloZNSTemplateExtension(models.Model):
    _inherit = 'zalo.zns.template'
    
    # Add debug fields
    last_test_date = fields.Datetime(string='Last Test Date')
    last_test_result = fields.Text(string='Last Test Result')
    debug_notes = fields.Text(string='Debug Notes')


class ZaloZNSHistoryExtension(models.Model):
    _inherit = 'zalo.zns.history'
    
    debug_info = fields.Text(string='Debug Info', groups="base.group_system")
    
    def retry_send(self):
        """Retry sending a failed notification"""
        self.ensure_one()
        
        if self.status != 'failed':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cannot Retry'),
                    'message': _('Only failed notifications can be retried.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        # Check if original record still exists
        if not self.model or not self.res_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cannot Retry'),
                    'message': _('Original record information is missing.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        original_record = self.env[self.model].browse(self.res_id)
        if not original_record.exists():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cannot Retry'),
                    'message': _('Original record no longer exists.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        # Only retry if the record has the send method
        if not hasattr(original_record, '_send_zns_notification'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cannot Retry'),
                    'message': _('Record type does not support sending notifications.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        # Add debug log
        self.env['zalo.zns.debug.log'].add_log(
            title=f"Retrying notification #{self.id}",
            content=f"Manual retry for notification to {self.phone} using template '{self.template_id.name}'",
            level='info',
            model='zalo.zns.history',
            res_id=self.id
        )
        
        # Retry sending
        try:
            result = original_record._send_zns_notification(self.template_id)
            return result
        except Exception as e:
            error_details = traceback.format_exc()
            
            # Log the error
            self.env['zalo.zns.debug.log'].add_log(
                title=f"Retry failed for notification #{self.id}",
                content=f"Error: {str(e)}\n\n{error_details}",
                level='error',
                model='zalo.zns.history',
                res_id=self.id
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Retry Failed'),
                    'message': _('Failed to retry notification: %s') % str(e),
                    'sticky': False,
                    'type': 'danger',
                }
            }