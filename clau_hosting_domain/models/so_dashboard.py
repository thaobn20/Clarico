from odoo import api, fields, models
from datetime import timedelta

class SOServiceDashboard(models.Model):
    _name = 'so.service.dashboard'
    _description = 'Sales Order Service Dashboard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Email notification tracking
    notification_30_sent = fields.Boolean('30-Day Notification Sent', default=False)
    notification_30_date = fields.Datetime('30-Day Notification Date')
    notification_15_sent = fields.Boolean('15-Day Notification Sent', default=False)
    notification_15_date = fields.Datetime('15-Day Notification Date')
    notification_5_sent = fields.Boolean('5-Day Notification Sent', default=False)
    notification_5_date = fields.Datetime('5-Day Notification Date')
    last_notification_text = fields.Html('Last Notification Text', readonly=True)
    
    # Add this field to allow configurable notification days
    notification_days = fields.Char('Notification Days', 
                                  default='30,15,5',
                                  help="Comma-separated list of days before expiration to send notifications")
    
    name = fields.Char('Name', required=True, tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', required=True, tracking=True)
    customer_id = fields.Many2one('res.partner', related='sale_order_id.partner_id', string='Customer', store=True)
    
    # Date fields
    start_date = fields.Date('Start Date', default=fields.Date.today, tracking=True)
    end_date = fields.Date('End Date', tracking=True)
    
    # Status fields
    status = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended')
    ], string='Status', compute='_compute_status', store=True, tracking=True)
    
    days_to_expire = fields.Integer(compute='_compute_days_to_expire', string='Days to Expire', store=True)
    
    # Service links
    domain_ids = fields.Many2many('domain.service', string='Domains', copy=False)
    hosting_ids = fields.Many2many('hosting.service', string='Hosting Services', copy=False)
    
    # Extensions

    extension_ids = fields.Many2many(
        'service.extension',
        'so_dashboard_extension_rel',
        'dashboard_id',
        'extension_id',
        string='Extensions'
    )
        
    # Statistics
    domain_count = fields.Integer(compute='_compute_counts', string='Domain Count')
    hosting_count = fields.Integer(compute='_compute_counts', string='Hosting Count')
    extension_count = fields.Integer(compute='_compute_counts', string='Extension Count')
    total_value = fields.Float(compute='_compute_total_value', string='Total Value')
    
    @api.depends('domain_ids', 'hosting_ids', 'extension_ids')
    def _compute_counts(self):
        for record in self:
            record.domain_count = len(record.domain_ids)
            record.hosting_count = len(record.hosting_ids)
            record.extension_count = len(record.extension_ids) if hasattr(record, 'extension_ids') else 0
    
    @api.depends('domain_ids.service_value', 'hosting_ids.service_value', 'extension_ids.price')
    def _compute_total_value(self):
        for record in self:
            domain_value = sum(record.domain_ids.mapped('service_value') or [0])
            hosting_value = sum(record.hosting_ids.mapped('service_value') or [0])
            extension_value = sum(record.extension_ids.mapped('price') or [0]) if hasattr(record, 'extension_ids') else 0
            record.total_value = domain_value + hosting_value + extension_value
    
    @api.depends('end_date')
    def _compute_status(self):
        today = fields.Date.today()
        for rec in self:
            if not rec.end_date:
                rec.status = 'active'
            elif rec.end_date < today:
                rec.status = 'expired'
            else:
                rec.status = 'active'
    
    @api.depends('end_date')
    def _compute_days_to_expire(self):
        today = fields.Date.today()
        for rec in self:
            if rec.end_date:
                delta = (rec.end_date - today).days
                rec.days_to_expire = delta if delta >= 0 else 0
            else:
                rec.days_to_expire = 0
    
    def action_view_domains(self):
        """View domains linked to this dashboard"""
        self.ensure_one()
        action = self.env.ref('clau_hosting_domain.action_domain_service').read()[0]
        
        if self.domain_count > 1:
            action['domain'] = [('id', 'in', self.domain_ids.ids)]
        elif self.domain_count == 1:
            action['views'] = [(self.env.ref('clau_hosting_domain.view_domain_service_form').id, 'form')]
            action['res_id'] = self.domain_ids.id
        
        return action
    
    def action_view_hosting(self):
        """View hosting services linked to this dashboard"""
        self.ensure_one()
        action = self.env.ref('clau_hosting_domain.action_hosting_service').read()[0]
        
        if self.hosting_count > 1:
            action['domain'] = [('id', 'in', self.hosting_ids.ids)]
        elif self.hosting_count == 1:
            action['views'] = [(self.env.ref('clau_hosting_domain.view_hosting_service_form').id, 'form')]
            action['res_id'] = self.hosting_ids.id
        
        return action
    
    def action_view_sale_order(self):
        """View the linked sales order"""
        self.ensure_one()
        action = self.env.ref('sale.action_orders').read()[0]
        action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        action['res_id'] = self.sale_order_id.id
        return action
    
    def update_service_dates(self):
        """Update all linked services with the dashboard dates"""
        self.ensure_one()
        if self.start_date and self.end_date:
            # Update domains
            if self.domain_ids:
                self.domain_ids.write({
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                })
            
            # Update hosting
            if self.hosting_ids:
                self.hosting_ids.write({
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                })
            
            # Update extensions if they exist
            if hasattr(self, 'extension_ids') and self.extension_ids:
                self.extension_ids.write({
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Service dates have been updated',
                    'type': 'success',
                }
            }
        return True
    
    def action_view_extensions(self):
        """View extensions linked to this dashboard"""
        self.ensure_one()
        if not hasattr(self, 'extension_ids'):
            return True
            
        action = self.env.ref('clau_hosting_domain.action_service_extension').read()[0]
        
        if self.extension_count > 1:
            action['domain'] = [('dashboard_id', '=', self.id)]
        elif self.extension_count == 1:
            action['views'] = [(self.env.ref('clau_hosting_domain.view_service_extension_form').id, 'form')]
            action['res_id'] = self.extension_ids.id
        
        return action
    
    def action_add_extension(self):
        """Add a new extension to this dashboard"""
        self.ensure_one()
        
        # Prepare a context with default values
        ctx = {
            'default_dashboard_id': self.id,
            'default_start_date': self.start_date,
            'default_end_date': self.end_date,
        }
        
        # If we have exactly one service of each type, set them as default
        if len(self.domain_ids) == 1:
            ctx['default_service_type'] = 'domain.service'
            ctx['default_service_id'] = f'domain.service,{self.domain_ids.id}'
        elif len(self.hosting_ids) == 1:
            ctx['default_service_type'] = 'hosting.service'
            ctx['default_service_id'] = f'hosting.service,{self.hosting_ids.id}'
        
        # Return action to create new extension
        return {
            'name': 'Add Extension',
            'type': 'ir.actions.act_window',
            'res_model': 'service.extension',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }
        
        def action_send_expiry_notification(self):
            """Manually send an expiry notification email"""
            self.ensure_one()
            if self.customer_id and self.customer_id.email:
                template = self.env.ref('clau_hosting_domain.email_template_service_expiry')
                if template:
                    # Determine which notification to send based on days to expire
                    if self.days_to_expire <= 5:
                        notification_type = '5-day'
                    elif self.days_to_expire <= 15:
                        notification_type = '15-day'
                    else:
                        notification_type = '30-day'
                        
                    self._send_expiry_notification(self, template, notification_type)
                    
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Notification Sent',
                            'message': f'Expiry notification sent to {self.customer_id.name}',
                            'type': 'success',
                        }
                    }
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'Could not send notification. Check that the customer has an email address.',
                    'type': 'danger',
                }
            }

            def action_reset_notifications(self):
                """Reset notification status flags"""
                self.ensure_one()
                self.write({
                    'notification_30_sent': False,
                    'notification_30_date': False,
                    'notification_15_sent': False,
                    'notification_15_date': False,
                    'notification_5_sent': False,
                    'notification_5_date': False
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Status Reset',
                        'message': 'Notification statuses have been reset',
                        'type': 'success',
                    }
                }
                
            def _cron_check_service_expiration(self):
                """
                Check for expiring services and send email notifications
                This method is called by the scheduled action
                """
                # Find all active services with end dates
                today = fields.Date.today()
                active_services = self.search([
                    ('end_date', '!=', False),
                    ('status', '=', 'active')
                ])
                
                # Send email notifications based on days to expire
                template = self.env.ref('clau_hosting_domain.email_template_service_expiry')
                if template:
                    for service in active_services:
                        # Skip if customer has no email address
                        if not service.customer_id or not service.customer_id.email:
                            continue
                            
                        # Get notification days from configuration or use defaults
                        try:
                            notification_days = [int(days.strip()) for days in service.notification_days.split(',') if days.strip()]
                            if not notification_days:
                                notification_days = [30, 15, 5]
                        except:
                            notification_days = [30, 15, 5]
                        
                        # Check if we need to send a notification based on days to expire
                        if service.days_to_expire in notification_days:
                            # Determine which notification we're sending
                            if service.days_to_expire == 30 and not service.notification_30_sent:
                                # 30-day notification
                                self._send_expiry_notification(service, template, '30-day')
                                service.write({
                                    'notification_30_sent': True,
                                    'notification_30_date': fields.Datetime.now()
                                })
                                
                            elif service.days_to_expire == 15 and not service.notification_15_sent:
                                # 15-day notification
                                self._send_expiry_notification(service, template, '15-day')
                                service.write({
                                    'notification_15_sent': True,
                                    'notification_15_date': fields.Datetime.now()
                                })
                                
                            elif service.days_to_expire == 5 and not service.notification_5_sent:
                                # 5-day notification
                                self._send_expiry_notification(service, template, '5-day')
                                service.write({
                                    'notification_5_sent': True,
                                    'notification_5_date': fields.Datetime.now()
                                })
                                
                            # Also create an activity for the account manager
                            self.env['mail.activity'].create({
                                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                                'note': f"{service.days_to_expire}-day notification sent to {service.customer_id.name} for {service.name}",
                                'user_id': service.create_uid.id or self.env.user.id,
                                'res_id': service.id,
                                'res_model_id': self.env['ir.model'].search([('model', '=', 'so.service.dashboard')], limit=1).id,
                                'summary': f"Service expiring in {service.days_to_expire} days",
                                'date_deadline': today + timedelta(days=3)
                            })
                
                return True

                def _send_expiry_notification(self, service, template, notification_type):
                    """Helper method to send and log a notification email"""
                    # Prepare the context for the template
                    ctx = {
                        'notification_type': notification_type,
                        'days_remaining': service.days_to_expire
                    }
                    
                    # Render the template with the context to get the content
                    body_html = template.with_context(ctx)._render_template(
                        template.body_html, 
                        template.model, 
                        service.id
                    )
                    
                    # Send the email
                    template.with_context(ctx).send_mail(service.id, force_send=True)
                    
                    # Save the email text for the notification log
                    service.last_notification_text = body_html
                    
                    # Log the message in the chatter
                    service.message_post(
                        body=f"Sent {notification_type} expiration notification to {service.customer_id.name}",
                        subject=f"Service Expiry - {notification_type}",
                        message_type='notification'
                    )
                def action_send_expiry_notification(self):
                    """Manually send an expiry notification email"""
                    self.ensure_one()
                    if self.customer_id and self.customer_id.email:
                        template = self.env.ref('clau_hosting_domain.email_template_service_expiry')
                        if template:
                            # Determine which notification to send based on days to expire
                            if self.days_to_expire <= 5:
                                notification_type = '5-day'
                            elif self.days_to_expire <= 15:
                                notification_type = '15-day'
                            else:
                                notification_type = '30-day'
                                
                            # Call the helper method to send the notification
                            self._send_expiry_notification(self, template, notification_type)
                            
                            return {
                                'type': 'ir.actions.client',
                                'tag': 'display_notification',
                                'params': {
                                    'title': 'Notification Sent',
                                    'message': f'Expiry notification sent to {self.customer_id.name}',
                                    'type': 'success',
                                }
                            }
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Error',
                            'message': 'Could not send notification. Check that the customer has an email address.',
                            'type': 'danger',
                        }
                    }

                def action_reset_notifications(self):
                    """Reset notification status flags"""
                    self.ensure_one()
                    self.write({
                        'notification_30_sent': False,
                        'notification_30_date': False,
                        'notification_15_sent': False,
                        'notification_15_date': False,
                        'notification_5_sent': False,
                        'notification_5_date': False
                    })
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Status Reset',
                            'message': 'Notification statuses have been reset',
                            'type': 'success',
                        }
                    }