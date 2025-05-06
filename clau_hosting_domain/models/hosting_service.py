from odoo import api, fields, models
from datetime import timedelta

class HostingService(models.Model):
    _name = 'hosting.service'
    _inherit = ['service.common.mixin']
    _description = 'Hosting Management'

    hosting_provider = fields.Selection([
        ('aws', 'Amazon Web Services'),
        ('gcp', 'Google Cloud Platform'),
        ('azure', 'Microsoft Azure'),
        ('digitalocean', 'DigitalOcean'),
        ('other', 'Other Provider')
    ], string='Hosting Provider', required=True, tracking=True)
    
    domain_id = fields.Many2one('domain.service', string='Linked Domain', tracking=True)
    storage = fields.Float('Storage (GB)', tracking=True)
    bandwidth = fields.Float('Bandwidth (GB)', tracking=True)
    server_type = fields.Selection([
        ('shared', 'Shared Hosting'),
        ('vps', 'VPS'),
        ('dedicated', 'Dedicated Server'),
        ('cloud', 'Cloud Instance')
    ], string='Server Type', default='shared', tracking=True)
    
    ip_address = fields.Char('IP Address')
    admin_url = fields.Char('Admin Panel URL')
    admin_username = fields.Char('Admin Username')
    admin_password = fields.Char('Admin Password')
    
    def name_get(self):
        result = []
        for hosting in self:
            name = hosting.name
            if hosting.domain_id:
                name = f"{name} ({hosting.domain_id.name})"
            result.append((hosting.id, name))
        return result
    
    def action_view_domain(self):
        """Open the linked domain in a form view"""
        self.ensure_one()
        if not self.domain_id:
            return False
            
        action = self.env.ref('clau_hosting_domain.action_domain_service').read()[0]
        action['views'] = [(self.env.ref('clau_hosting_domain.view_domain_service_form').id, 'form')]
        action['res_id'] = self.domain_id.id
        return action
    
    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        """When customer changes, filter domain_id to show only domains of this customer"""
        if self.customer_id:
            # Clear domain_id if it doesn't belong to the selected customer
            if self.domain_id and self.domain_id.customer_id != self.customer_id:
                self.domain_id = False
            
            # Return a domain to filter available domains
            return {'domain': {'domain_id': [('customer_id', '=', self.customer_id.id)]}}
        else:
            self.domain_id = False
    
    @api.model
    def _cron_check_hosting_expiration(self):
        """
        Scheduled action to check for hosting services expiring soon
        and send email notifications or create activities
        """
        # Hosting expiring in 30 days
        hosting_30 = self.search([
            ('end_date', '>=', fields.Date.today()),
            ('end_date', '<=', fields.Date.today() + timedelta(days=30)),
            ('status', '=', 'active')
        ])
        
        # Hosting expiring in 15 days
        hosting_15 = self.search([
            ('end_date', '>=', fields.Date.today()),
            ('end_date', '<=', fields.Date.today() + timedelta(days=15)),
            ('status', '=', 'active')
        ])
        
        # Send email notifications
        template_id = self.env.ref('clau_hosting_domain.email_template_hosting_expiry')
        
        for hosting in hosting_30:
            # Only send email if not auto-renew
            if not hosting.auto_renew:
                template_id.send_mail(hosting.id, force_send=True)
        
        # Create activities for hosting expiring in 15 days
        for hosting in hosting_15:
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'note': f"Hosting service {hosting.name} expires in {hosting.days_to_expire} days",
                'user_id': self.env.user.id,
                'res_id': hosting.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'hosting.service')], limit=1).id,
                'summary': "Hosting service expiring soon",
                'date_deadline': fields.Date.today() + timedelta(days=5)
            })
        
        return True