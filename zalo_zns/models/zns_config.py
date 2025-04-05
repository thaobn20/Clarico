from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
import json
import logging
import traceback
import pprint

_logger = logging.getLogger(__name__)

class ZaloZNSConfig(models.Model):
    _name = 'zalo.zns.config'
    _description = 'Zalo ZNS Configuration'

    name = fields.Char(string='Name', required=True, default='ZNS Configuration')
    api_url = fields.Char(string='API URL', required=True, default='https://zns.bom.asia/api/v1')
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
    
    # Test connection API
    def test_connection(self):
        try:
            # Directly try the template-params endpoint first with proper debugging
            base_url = self.api_url.rstrip('/')
            if not base_url.endswith('/v1'):
                if '/api/v1' not in base_url:
                    base_url = f"{base_url}/api/v1"
            
            # Ensure we have the correct endpoint
            params_url = f"{base_url}/template-params"
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            if self.debug_mode:
                _logger.info("=== ZNS DEBUG: Testing API connection ===")
                _logger.info("URL: %s", params_url)
                _logger.info("Headers: %s", pprint.pformat(headers))
            
            # This endpoint requires a POST with empty JSON body
            params_response = requests.post(params_url, headers=headers, json={}, timeout=15)
            
            if self.debug_mode:
                _logger.info("Response Status: %s", params_response.status_code)
                _logger.info("Response Headers: %s", pprint.pformat(dict(params_response.headers)))
                _logger.info("Response Body: %s", params_response.text[:1000] if len(params_response.text) > 1000 else params_response.text)
            
            # Check response and handle common issues
            if params_response.status_code == 404:
                # Try alternative URL structure
                alternative_url = f"https://zns.bom.asia/api/v1/template-params"
                if params_url != alternative_url:
                    if self.debug_mode:
                        _logger.info("404 error - trying alternative URL: %s", alternative_url)
                    
                    params_response = requests.post(alternative_url, headers=headers, json={}, timeout=15)
                    
                    if self.debug_mode:
                        _logger.info("Alternative Response Status: %s", params_response.status_code)
                        _logger.info("Alternative Response Body: %s", params_response.text[:1000] if len(params_response.text) > 1000 else params_response.text)
                    
                    if params_response.status_code == 404:
                        raise UserError(_(
                            "API endpoint not found at %s or %s.\n\n"
                            "Please verify your API URL configuration. "
                            "The correct URL format should be: https://zns.bom.asia/api/v1"
                        ) % (params_url, alternative_url))
            
            # Parse response
            try:
                params_result = params_response.json() if params_response.text else {}
            except json.JSONDecodeError:
                params_result = {"error": "invalid_json", "message": "Invalid JSON response"}
                if self.debug_mode:
                    _logger.error("Failed to parse JSON response: %s", params_response.text[:500])
            
            # Handle authentication errors
            if params_response.status_code == 401 or (isinstance(params_result, dict) and params_result.get('error') in ['-103', '-104']):
                raise UserError(_("Authentication failed. Please check your API key."))
            
            # Success case
            if params_response.status_code == 200 and isinstance(params_result, dict) and params_result.get('error') == '0':
                # Successfully connected! Update the API URL if needed
                if params_url != self.api_url and params_url.startswith("https://zns.bom.asia/api/v1"):
                    self.api_url = "https://zns.bom.asia/api/v1"
                    if self.debug_mode:
                        _logger.info("Updated API URL to correct value: %s", self.api_url)
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Test'),
                        'message': _('Connection successful! API is accessible and credentials are valid.'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                # Other error
                error_code = params_result.get('error') if isinstance(params_result, dict) else 'unknown'
                error_msg = params_result.get('message') if isinstance(params_result, dict) else params_response.text
                
                user_error = self._handle_zns_error(error_code, error_msg)
                raise UserError(_("API Error: %s") % user_error)
                
        except requests.exceptions.ConnectionError as e:
            if self.debug_mode:
                _logger.error("=== ZNS DEBUG: Connection error ===")
                _logger.error("Exception: %s", str(e))
            raise UserError(_("Cannot connect to ZNS server. Please check your internet connection and firewall settings."))
        except requests.exceptions.Timeout as e:
            if self.debug_mode:
                _logger.error("=== ZNS DEBUG: Connection timeout ===")
                _logger.error("Exception: %s", str(e))
            raise UserError(_("Connection to ZNS server timed out. The server might be slow or unreachable."))
        except UserError:
            # Re-raise UserError as is
            raise
        except Exception as e:
            error_details = traceback.format_exc()
            if self.debug_mode:
                _logger.error("=== ZNS DEBUG: Connection test exception ===")
                _logger.error("Exception: %s", str(e))
                _logger.error("Traceback: %s", error_details)
            raise UserError(_("Connection failed: %s\n\nDetails: %s") % (str(e), error_details))
            
    # Enhanced template fetching with debugging
    def fetch_templates(self):
        self.ensure_one()
        try:
            if self.debug_mode:
                _logger.info("=== ZNS DEBUG: Fetching templates with config ID %s ===", self.id)
            
            # Correct the endpoint structure
            base_url = self.api_url.rstrip('/')
            if not base_url.endswith('/v1'):
                if '/api/v1' not in base_url:
                    base_url = f"{base_url}/api/v1"
                    
            endpoint = f"{base_url}/template-params"
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            if self.debug_mode:
                _logger.info("Fetching templates from endpoint: %s", endpoint)
                _logger.info("With headers: %s", pprint.pformat(headers))
            
            # POST request instead of GET
            response = requests.post(endpoint, headers=headers, json={}, timeout=15)
            
            if self.debug_mode:
                _logger.info("Response Status: %s", response.status_code)
                _logger.info("Response Headers: %s", pprint.pformat(dict(response.headers)))
                _logger.info("Response Body: %s", response.text[:1000] if len(response.text) > 1000 else response.text)
            
            # Parse the response
            try:
                result = response.json() if response.text else {}
            except json.JSONDecodeError:
                result = {"error": "invalid_json", "message": "Invalid JSON response"}
                if self.debug_mode:
                    _logger.error("Failed to parse JSON response: %s", response.text[:500])
            
            if response.status_code == 200 and isinstance(result, dict) and result.get('error') == '0':
                templates_data = result.get('data', [])
                
                if self.debug_mode:
                    _logger.info("Fetched %s templates", len(templates_data))
                
                template_model = self.env['zalo.zns.template']
                parameter_model = self.env['zalo.zns.template.parameter']
                
                for template in templates_data:
                    template_name = template.get('title', template.get('name', ''))
                    template_id = template.get('template_id', template.get('id', ''))
                    
                    if not template_id:
                        if self.debug_mode:
                            _logger.warning("Skipping template without ID: %s", template)
                        continue
                        
                    if self.debug_mode:
                        _logger.info("Processing template: %s (ID: %s)", template_name, template_id)
                        
                    existing = template_model.search([
                        ('template_id', '=', template_id),
                        ('company_id', '=', self.company_id.id)
                    ], limit=1)
                    
                    template_vals = {
                        'name': template_name,
                        'template_id': template_id,
                        'template_code': template.get('code', ''),
                        'template_content': template.get('content', ''),
                        'status': template.get('status', 'active'),
                        'company_id': self.company_id.id,
                    }
                    
                    # Handle parameters
                    params = template.get('params', [])
                    
                    if existing:
                        if self.debug_mode:
                            _logger.info("Updating existing template ID: %s", existing.id)
                        existing.write(template_vals)
                        
                        # Clear old parameters
                        existing.parameter_ids.unlink()
                        
                        # Add new parameters
                        for param in params:
                            parameter_model.create({
                                'name': param.get('name', ''),
                                'type': param.get('type', 'text').lower(),
                                'required': param.get('require', False),
                                'description': param.get('title', ''),
                                'template_id': existing.id,
                            })
                    else:
                        if self.debug_mode:
                            _logger.info("Creating new template")
                        new_template = template_model.create(template_vals)
                        
                        # Add parameters
                        for param in params:
                            parameter_model.create({
                                'name': param.get('name', ''),
                                'type': param.get('type', 'text').lower(),
                                'required': param.get('require', False),
                                'description': param.get('title', ''),
                                'template_id': new_template.id,
                            })
                        
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
                error_code = result.get('error') if isinstance(result, dict) else 'unknown'
                error_message = result.get('message', 'Unknown error') if isinstance(result, dict) else response.text
                
                user_error = self._handle_zns_error(error_code, error_message)
                
                if self.debug_mode:
                    _logger.error("=== ZNS DEBUG: Template fetch failed ===")
                    _logger.error("Error: %s", user_error)
                
                raise UserError(_('Failed to fetch templates: %s') % user_error)
                
        except UserError:
            # Re-raise UserError as is
            raise
        except Exception as e:
            error_details = traceback.format_exc()
            
            if self.debug_mode:
                _logger.error("=== ZNS DEBUG: Template fetch exception ===")
                _logger.error("Exception: %s", str(e))
                _logger.error("Traceback: %s", error_details)
                
            raise UserError(_('Failed to fetch templates: %s\n\nDetails: %s') % (str(e), error_details))
    
    # Sending Message
    def send_zns_message(self, phone, template_id, params=None):
        """
        Send a ZNS message using the configured API
        
        :param phone: Phone number to send to (will be formatted if needed)
        :param template_id: Template ID to use
        :param params: Dictionary of parameters to fill into the template
        :return: Result dictionary
        """
        self.ensure_one()
        
        if not params:
            params = {}
            
        try:
            # Format the phone number if needed
            if not phone.startswith('+84') and not phone.startswith('84'):
                if phone.startswith('0'):
                    phone = '84' + phone[1:]
                else:
                    phone = '84' + phone
            
            # Construct the URL
            base_url = self.api_url.rstrip('/')
            if not base_url.endswith('/v1'):
                if '/api/v1' not in base_url:
                    base_url = f"{base_url}/api/v1"
                    
            endpoint = f"{base_url}/send-template"
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Prepare the payload according to the API docs
            payload = {
                'phone': phone,
                'params': params
            }
            
            if self.debug_mode:
                _logger.info("=== ZNS DEBUG: Sending template message ===")
                _logger.info("URL: %s", endpoint)
                _logger.info("Headers: %s", pprint.pformat(headers))
                _logger.info("Payload: %s", pprint.pformat(payload))
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=15)
            
            if self.debug_mode:
                _logger.info("Response Status: %s", response.status_code)
                _logger.info("Response Headers: %s", pprint.pformat(dict(response.headers)))
                _logger.info("Response Body: %s", response.text[:1000] if len(response.text) > 1000 else response.text)
            
            # Parse the response
            try:
                result = response.json() if response.text else {}
            except json.JSONDecodeError:
                result = {"error": "invalid_json", "message": "Invalid JSON response"}
                if self.debug_mode:
                    _logger.error("Failed to parse JSON response: %s", response.text[:500])
            
            if response.status_code == 200 and isinstance(result, dict) and result.get('error') == '0':
                return {
                    'success': True,
                    'message_id': result.get('data', {}).get('message_id'),
                    'details': result
                }
            else:
                error_code = result.get('error', 'unknown') if isinstance(result, dict) else 'unknown'
                error_msg = result.get('message', 'Unknown error') if isinstance(result, dict) else response.text
                
                user_error = self._handle_zns_error(error_code, error_msg)
                
                return {
                    'success': False,
                    'error_code': error_code,
                    'error_message': user_error,
                    'details': result
                }
                
        except Exception as e:
            error_details = traceback.format_exc()
            if self.debug_mode:
                _logger.error("=== ZNS DEBUG: Send message exception ===")
                _logger.error("Exception: %s", str(e))
                _logger.error("Traceback: %s", error_details)
            
            return {
                'success': False,
                'error_code': 'exception',
                'error_message': str(e),
                'details': error_details
            }
    
    # Error Handling
    def _handle_zns_error(self, error_code, error_message):
        """Parse and handle ZNS error codes with appropriate messages"""
        error_mapping = {
            '-101': _('Phone number invalid or empty'),
            '-102': _('IP address invalid'),
            '-103': _('Secret key empty'),
            '-104': _('Secret key not exist'),
            '-105': _('IP address not authorized'),
            '-106': _('Template ID not exists'),
            '-107': _('Template ID invalid'),
            '-108': _('Template data empty'),
            '-110': _('Out of quota'),
            '-112': _('Parameter invalid'),
            '-113': _('Template data invalid'),
            '-118': _('Zalo account not existed')
            # Add other error codes as needed
        }
        
        # If error code is known, return the friendly message
        user_message = error_mapping.get(str(error_code), error_message)
        return user_message


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
    
def action_test_template(self):
    """
    Open a wizard to test sending this template to a specific number
    """
    self.ensure_one()
    return {
        'name': _('Test Template'),
        'type': 'ir.actions.act_window',
        'view_mode': 'form',
        'res_model': 'zalo.zns.template.test',  # This wizard model needs to be created
        'target': 'new',
        'context': {
            'default_template_id': self.id,
        },
    }

def action_preview_template(self):
    """
    Display a preview of how the template will look
    """
    self.ensure_one()
    # Get parameters
    params = {}
    for param in self.parameter_ids:
        # Generate sample data based on parameter type
        if param.type == 'number':
            params[param.name] = '123456'
        elif param.type == 'url':
            params[param.name] = 'https://example.com'
        elif param.type == 'email':
            params[param.name] = 'example@example.com'
        elif param.type == 'date':
            params[param.name] = '01/01/2025'
        else:  # text or default
            params[param.name] = f'Sample {param.name}'
    
    # Generate preview
    content = self.template_content
    for name, value in params.items():
        content = content.replace(f'<{name}>', value)
    
    return {
        'name': _('Template Preview'),
        'type': 'ir.actions.act_window',
        'view_mode': 'form',
        'res_model': 'zalo.zns.template.preview',  # This model needs to be created
        'target': 'new',
        'context': {
            'default_template_id': self.id,
            'default_content_preview': content,
            'default_parameters': str(params),
        },
    }