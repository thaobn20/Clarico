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
