from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
import json
import logging
import traceback

_logger = logging.getLogger(__name__)

class ZaloZNSConfig(models.Model):
    _name = 'zalo.zns.config'
    _description = 'Zalo ZNS Configuration'

    name = fields.Char(string='Name', required=True, default='ZNS Configuration')
    api_url = fields.Char(string='API URL', required=True, default='https://zns.bom.asia/api/v1/send-template')
    api_key = fields.Char(string='API Key', required=True)
    active = fields.Boolean(default=True)
    template_fetch_date = fields.Datetime(string='Last Template Fetch Date')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # For direct Zalo API integration (alternative)
    use_direct_api = fields.Boolean(string='Use Direct Zalo API', default=False)
    zalo_app_id = fields.Char(string='Zalo App ID')
    zalo_app_secret = fields.Char(string='Zalo App Secret')
    zalo_access_token = fields.Char(string='Zalo Access Token')
    zalo_refresh_token = fields.Char(string='Zalo Refresh Token')
    zalo_token_expire = fields.Datetime(string='Token Expiry Date')
    
    # Debug-related fields
    debug_mode = fields.Boolean(string='Debug Mode', default=False,
                               help='Enable detailed logging for troubleshooting')
    test_mode = fields.Boolean(string='Test Mode', default=False,
                              help='Use test endpoint and avoid sending real notifications')
    log_retention_days = fields.Integer(string='Log Retention (Days)', default=30,
                                       help='Number of days to keep detailed logs')
    
    _sql_constraints = [
        ('company_config_unique', 
         'UNIQUE(company_id)', 
         'Only one ZNS configuration allowed per company!')
    ]
    # Other fields...
def test_connection(self):
    try:
        # If template_id is part of the URL
        template_id = self.template_id  # Get from your model
        url = f"https://zns.bom.asia/api/v1/send-template/{template_id}"
        
        # Or if template_id is in the payload
        # url = "https://zns.bom.asia/api/v1/send-template"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "app_id": self.app_id,
            # Include other required parameters
            # "template_id": self.template_id,  # If needed in payload
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return {'success': True, 'message': 'Connection successful!'}
        else:
            raise UserError(
                f"Connection failed: Status code: {response.status_code}, Response: {response.text}"
            )
    except Exception as e:
        error_details = traceback.format_exc()
        raise UserError(f"Connection failed: {str(e)}\n\nDetails: {error_details}")
            
    # Enhanced template fetching with debugging
    def fetch_templates(self):
        self.ensure_one()
        try:
            if self.debug_mode:
                _logger.info("=== ZNS DEBUG: Fetching templates with config ID %s ===", self.id)
                
            if self.use_direct_api:
                # Implementation for direct Zalo API
                pass
            else:
                # Fetch templates from ZNS.BOM.ASIA
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                endpoint = f'{self.api_url.rstrip("/")}/templates'
                
                if self.debug_mode:
                    _logger.info("Fetching templates from endpoint: %s", endpoint)
                    _logger.info("With headers: %s", pprint.pformat(headers))
                
                response = requests.get(endpoint, headers=headers)
                
                if self.debug_mode:
                    _logger.info("Response Status: %s", response.status_code)
                    _logger.info("Response Headers: %s", pprint.pformat(dict(response.headers)))
                    _logger.info("Response Body Preview: %s", response.text[:1000] if len(response.text) > 1000 
                                else response.text)
                
            if response.status_code == 200:
                templates_data = response.json().get('data', [])
                
                if self.debug_mode:
                    _logger.info("Fetched %s templates", len(templates_data))
                    
                template_model = self.env['zalo.zns.template']
                
                for template in templates_data:
                    if self.debug_mode:
                        _logger.info("Processing template: %s", template.get('name'))
                        
                    existing = template_model.search([
                        ('template_id', '=', template.get('id')),
                        ('company_id', '=', self.company_id.id)
                    ], limit=1)
                    
                    template_vals = {
                        'name': template.get('name'),
                        'template_id': template.get('id'),
                        'template_code': template.get('code'),
                        'template_content': template.get('content'),
                        'status': template.get('status'),
                        'company_id': self.company_id.id,
                    }
                    
                    if existing:
                        if self.debug_mode:
                            _logger.info("Updating existing template ID: %s", existing.id)
                        existing.write(template_vals)
                    else:
                        if self.debug_mode:
                            _logger.info("Creating new template")
                        template_model.create(template_vals)
                        
                self.template_fetch_date = fields.Datetime.now()
                
                if self.debug_mode:
                    _logger.info("=== ZNS DEBUG: Template fetch completed successfully ===")
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Templates Fetched'),
                        'message': _('%s templates have been synchronized.') % len(templates_data),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                error_message = f"Status code: {response.status_code}, Response: {response.text}"
                
                if self.debug_mode:
                    _logger.error("=== ZNS DEBUG: Template fetch failed ===")
                    _logger.error("Error: %s", error_message)
                
                raise UserError(
                    _('Failed to fetch templates: %s') % error_message
                )
                
        except Exception as e:
            error_details = traceback.format_exc()
            
            if self.debug_mode:
                _logger.error("=== ZNS DEBUG: Template fetch exception ===")
                _logger.error("Exception: %s", str(e))
                _logger.error("Traceback: %s", error_details)
                
            raise UserError(_('Failed to fetch templates: %s\n\nDetails: %s') % (str(e), error_details))