from odoo import api, fields, models
from datetime import timedelta

class DomainService(models.Model):
    _name = 'domain.service'
    _inherit = ['service.common.mixin']
    _description = 'Domain Management'
    end_date = fields.Date('End Date', tracking=True)
    domain_provider = fields.Selection([
        ('nhanhoa', 'Nhan Hoa (.vn)'),
        ('godaddy', 'GoDaddy'),
        ('namecheap', 'Namecheap'),
        ('other', 'Other Providers')
    ], string='Domain Registrar', required=True, tracking=True)
    
    domain_type = fields.Selection([
        ('vn', '.vn'),
        ('global', 'International')
    ], compute='_compute_domain_type', store=True)
    
    hosting_ids = fields.One2many('hosting.service', 'domain_id', string='Linked Hosting Services')
    # Add computed field for hosting count
    hosting_count = fields.Integer(string='Hosting Count', compute='_compute_hosting_count', store=True)
    
    registry_lock = fields.Boolean('Registry Lock', help="Domain is locked at registry level")
    nameservers = fields.Text('Nameservers')
    dns_setup_date = fields.Date('DNS Setup Date')
    
    @api.depends('name')
    def _compute_domain_type(self):
        for rec in self:
            rec.domain_type = 'vn' if rec.name and rec.name.endswith('.vn') else 'global'
    
    @api.depends('hosting_ids')
    def _compute_hosting_count(self):
        for record in self:
            record.hosting_count = len(record.hosting_ids)
    
    @api.model
    def create(self, vals):
        # Force lowercase domain names
        if vals.get('name'):
            vals['name'] = vals['name'].lower()
        return super(DomainService, self).create(vals)
    
    def write(self, vals):
        # Force lowercase domain names
        if vals.get('name'):
            vals['name'] = vals['name'].lower()
        return super(DomainService, self).write(vals)
    
    def name_get(self):
        result = []
        for domain in self:
            name = domain.name
            if domain.customer_id:
                name = f"{name} ({domain.customer_id.name})"
            result.append((domain.id, name))
        return result
    
    def action_view_hosting(self):
        """Open a view with the hosting services linked to this domain"""
        self.ensure_one()
        action = self.env.ref('clau_hosting_domain.action_hosting_service').read()[0]
        if self.hosting_count > 1:
            action['domain'] = [('domain_id', '=', self.id)]
        elif self.hosting_count == 1:
            action['views'] = [(self.env.ref('clau_hosting_domain.view_hosting_service_form').id, 'form')]
            action['res_id'] = self.hosting_ids.id
        else:
            action['context'] = {
                'default_domain_id': self.id,
                'default_customer_id': self.customer_id.id,
            }
        return action
    
    def action_add_hosting(self):
        """Action to add a new hosting service linked to this domain"""
        self.ensure_one()
        # Get the action
        action = self.env['ir.actions.act_window']._for_xml_id('clau_hosting_domain.action_hosting_service')
        # Update context with default values
        ctx = dict(
            self.env.context,
            default_domain_id=self.id,
            default_customer_id=self.customer_id.id,
        )
        action['context'] = ctx
        action['views'] = [(self.env.ref('clau_hosting_domain.view_hosting_service_form').id, 'form')]
        action['target'] = 'current'
        return action
    
    @api.model
    def _cron_check_domain_expiration(self):
        """
        Scheduled action to check for domains expiring soon
        and send email notifications or create activities
        """
        # Domains expiring in 30 days
        domains_30 = self.search([
            ('end_date', '>=', fields.Date.today()),
            ('end_date', '<=', fields.Date.today() + timedelta(days=30)),
            ('status', '=', 'active')
        ])
        
        # Domains expiring in 15 days
        domains_15 = self.search([
            ('end_date', '>=', fields.Date.today()),
            ('end_date', '<=', fields.Date.today() + timedelta(days=15)),
            ('status', '=', 'active')
        ])
        
        # Send email notifications
        template_id = self.env.ref('clau_hosting_domain.email_template_domain_expiry')
        
        for domain in domains_30:
            # Only send email if not auto-renew
            if not domain.auto_renew:
                template_id.send_mail(domain.id, force_send=True)
        
        # Create activities for domains expiring in 15 days
        for domain in domains_15:
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'note': f"Domain {domain.name} expires in {domain.days_to_expire} days",
                'user_id': self.env.user.id,
                'res_id': domain.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'domain.service')], limit=1).id,
                'summary': "Domain expiring soon",
                'date_deadline': fields.Date.today() + timedelta(days=5)
            })
        
        return True