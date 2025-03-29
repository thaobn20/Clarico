from odoo import api, fields, models, _

class ZaloZNSTemplate(models.Model):
    _name = 'zalo.zns.template'
    _description = 'Zalo ZNS Template'
    
    name = fields.Char(string='Template Name', required=True)
    template_id = fields.Char(string='Template ID', required=True)
    template_code = fields.Char(string='Template Code')
    template_content = fields.Text(string='Template Content')
    params = fields.One2many('zalo.zns.template.param', 'template_id', string='Parameters')
    status = fields.Selection([
        ('active', 'Active'),
        ('pending', 'Pending Approval'),
        ('rejected', 'Rejected'),
        ('inactive', 'Inactive')
    ], string='Status', default='active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    model_id = fields.Many2one('ir.model', string='Applies To')
    model_name = fields.Char(related='model_id.model', string='Model Name')
    
    # When the template is used
    trigger = fields.Selection([
        ('manual', 'Manual'),
        ('create', 'On Creation'),
        ('write', 'On Update'),
        ('stage_change', 'On Stage Change'),
        ('status_change', 'On Status Change'),
    ], string='Send Trigger', default='manual')
    
    # For Specific Documents
    is_so_template = fields.Boolean(string='Sales Order Template')
    is_po_template = fields.Boolean(string='Purchase Order Template')
    is_invoice_template = fields.Boolean(string='Invoice Template')
    
    _sql_constraints = [
        ('template_id_company_unique', 
         'UNIQUE(template_id, company_id)', 
         'Template ID must be unique per company!')
    ]

class ZaloZNSTemplateParam(models.Model):
    _name = 'zalo.zns.template.param'
    _description = 'Zalo ZNS Template Parameter'
    
    name = fields.Char(string='Parameter Name', required=True)
    field_id = fields.Many2one('ir.model.fields', string='Mapped Field')
    template_id = fields.Many2one('zalo.zns.template', string='Template')
    default_value = fields.Char(string='Default Value')
    sequence = fields.Integer(string='Sequence', default=10)
    is_required = fields.Boolean(string='Required', default=True)
    
class ZaloZNSTemplateExtension(models.Model):
    _inherit = 'zalo.zns.template'
    
    # Add debug fields
    last_test_date = fields.Datetime(string='Last Test Date')
    last_test_result = fields.Text(string='Last Test Result')
    debug_notes = fields.Text(string='Debug Notes')
    
class ZaloZNSTemplate(models.Model):
    _inherit = 'zalo.zns.template'
    
    def action_test_template(self):
        """Test the template without actually sending a notification"""
        self.ensure_one()
        
        config = self.env['zalo.zns.config'].search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            raise UserError(_('ZNS configuration not found.'))
            
        # Find a record to test with
        record = False
        
        if self.model_id:
            model_name = self.model_id.model
            
            if model_name == 'sale.order':
                record = self.env['sale.order'].search([
                    ('state', 'not in', ['draft', 'cancel']),
                    ('company_id', '=', self.company_id.id)
                ], limit=1)
            elif model_name == 'purchase.order':
                record = self.env['purchase.order'].search([
                    ('state', 'not in', ['draft', 'cancel']),
                    ('company_id', '=', self.company_id.id)
                ], limit=1)
            elif model_name == 'account.move':
                record = self.env['account.move'].search([
                    ('state', '=', 'posted'),
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                    ('company_id', '=', self.company_id.id)
                ], limit=1)
            else:
                record = self.env[model_name].search([], limit=1)
                
        if not record:
            raise UserError(_('No test record found for model %s. Please create a record first.') % 
                          (self.model_id.name or model_name))
        
        # Prepare a simulated test with debug logging
        test_result = {
            'template_id': self.id,
            'template_name': self.name,
            'record_id': record.id,
            'record_name': record.display_name if hasattr(record, 'display_name') else f"Record #{record.id}",
            'parameters': {},
            'errors': [],
            'warnings': []
        }
        
        # Log beginning of test
        self.env['zalo.zns.debug.log'].add_log(
            title=f"Template Test: {self.name}",
            content=f"Starting test for template '{self.name}' on {model_name} #{record.id}",
            level='info',
            model='zalo.zns.template',
            res_id=self.id
        )
        
        # Check for required parameters
        for param in self.params:
            param_result = {
                'name': param.name,
                'required': param.is_required,
                'field': param.field_id.name if param.field_id else None,
                'default': param.default_value,
                'value': None,
                'status': 'unknown'
            }
            
            if param.field_id:
                field_name = param.field_id.name
                
                # Check if field exists
                if not hasattr(record, field_name):
                    param_result['status'] = 'error'
                    param_result['message'] = f"Field '{field_name}' not found on model {model_name}"
                    test_result['errors'].append(f"Parameter '{param.name}': Field '{field_name}' not found")
                    continue
                
                # Get field value
                try:
                    field_value = record[field_name]
                    
                    # Process field value based on type
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
                    
                    param_result['value'] = field_value
                    param_result['status'] = 'success'
                    
                    # Check if value is empty but parameter is required
                    if param.is_required and (field_value is False or field_value == ''):
                        param_result['status'] = 'warning'
                        param_result['message'] = f"Required field '{field_name}' has no value, will use default"
                        test_result['warnings'].append(
                            f"Parameter '{param.name}': Required field '{field_name}' is empty")
                        
                        # Use default value
                        param_result['value'] = param.default_value or ''
                        
                except Exception as e:
                    param_result['status'] = 'error'
                    param_result['message'] = f"Error getting field value: {str(e)}"
                    test_result['errors'].append(f"Parameter '{param.name}': {str(e)}")
            else:
                # No field mapping, use default value
                param_result['value'] = param.default_value or ''
                param_result['status'] = 'default'
                
                if param.is_required and not param.default_value:
                    param_result['status'] = 'warning'
                    param_result['message'] = 'Required parameter has no field mapping or default value'
                    test_result['warnings'].append(
                        f"Parameter '{param.name}': Required but has no field mapping or default value")
            
            test_result['parameters'][param.name] = param_result
        
        # Test phone number availability
        try:
            if hasattr(record, 'partner_phone_normalized'):
                phone = record.partner_phone_normalized
            elif hasattr(record, 'partner_id') and hasattr(record.partner_id, 'mobile'):
                phone = record.partner_id.mobile or record.partner_id.phone
            else:
                phone = None
                
            if not phone:
                test_result['errors'].append("No phone number available for notification")
                
            test_result['phone'] = phone
        except Exception as e:
            test_result['errors'].append(f"Error getting phone number: {str(e)}")
        
        # Log test result
        result_summary = (
            f"Test completed with {len(test_result['errors'])} errors, "
            f"{len(test_result['warnings'])} warnings"
        )
        
        log_level = 'info'
        if test_result['errors']:
            log_level = 'error'
        elif test_result['warnings']:
            log_level = 'warning'
            
        self.env['zalo.zns.debug.log'].add_log(
            title=f"Template Test Result: {self.name}",
            content=f"{result_summary}\n\n{json.dumps(test_result, indent=2)}",
            level=log_level,
            model='zalo.zns.template',
            res_id=self.id
        )
        
        # Update template with test result
        self.write({
            'last_test_date': fields.Datetime.now(),
            'last_test_result': json.dumps(test_result, indent=2)
        })
        
        # Return wizard with test results
        return {
            'name': _('Template Test Results'),
            'type': 'ir.actions.act_window',
            'res_model': 'zalo.zns.template.test.result',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
                'default_test_result': json.dumps(test_result, indent=2),
                'default_has_errors': bool(test_result['errors']),
                'default_has_warnings': bool(test_result['warnings']),
                'default_record_id': record.id,
                'default_record_model': model_name,
            }
        }
        
    def action_preview_template(self):
        """Preview how the template will look with actual data"""
        self.ensure_one()
        
        # This is similar to test but focuses on visual preview
        return self.action_test_template()
    
    def retry_failed_notifications(self):
        """Retry sending all failed notifications using this template"""
        self.ensure_one()
        
        failed_notifications = self.env['zalo.zns.history'].search([
            ('template_id', '=', self.id),
            ('status', '=', 'failed')
        ])
        
        if not failed_notifications:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Failed Notifications'),
                    'message': _('There are no failed notifications to retry for this template.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        retry_count = 0
        success_count = 0
        
        for notification in failed_notifications:
            try:
                # Get original record
                if not notification.model or not notification.res_id:
                    continue
                    
                original_record = self.env[notification.model].browse(notification.res_id)
                if not original_record.exists():
                    continue
                    
                # Only retry if the record has the send method
                if hasattr(original_record, '_send_zns_notification'):
                    retry_count += 1
                    result = original_record._send_zns_notification(self)
                    
                    # Check if successful
                    if result and result.get('params', {}).get('type') == 'success':
                        success_count += 1
            except Exception as e:
                # Log error but continue with other notifications
                _logger.error("Failed to retry notification ID %s: %s", notification.id, str(e))
                continue
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Retry Complete'),
                'message': _('Retried %s notifications, %s successful.') % (retry_count, success_count),
                'sticky': False,
                'type': 'info',
            }
        }