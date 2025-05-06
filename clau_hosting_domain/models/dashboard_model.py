from odoo import api, fields, models, tools
from datetime import timedelta, date
import json

class ServiceDashboard(models.Model):
    _name = 'service.dashboard'
    _description = 'Service Dashboard'
    _auto = False  # This is a SQL view, not a regular table
    
    name = fields.Char(string='Name')
    
    # Statistics fields
    total_domains = fields.Integer(string='Total Domains', compute='_compute_statistics')
    total_hosting = fields.Integer(string='Total Hosting', compute='_compute_statistics')
    total_customers = fields.Integer(string='Total Customers', compute='_compute_statistics')
    expiring_domains = fields.Integer(string='Expiring Domains', compute='_compute_statistics')
    
    # Chart fields
    domain_provider_chart = fields.Char(string='Domain Providers Chart', compute='_compute_domain_provider_chart')
    hosting_provider_chart = fields.Char(string='Hosting Providers Chart', compute='_compute_hosting_provider_chart')
    expiring_domains_chart = fields.Char(string='Expiring Domains Chart', compute='_compute_expiring_domains_chart')
    services_by_customer_chart = fields.Char(string='Services by Customer Chart', compute='_compute_services_by_customer_chart')
    
    def init(self):
        """Initialize the SQL view for the dashboard"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                SELECT 1 as id, 'Dashboard' as name
            )
        ''' % self._table)
    
    @api.depends()
    def _compute_statistics(self):
        """Compute dashboard statistics"""
        for record in self:
            # Count active domains
            record.total_domains = self.env['domain.service'].search_count([
                ('status', '=', 'active')
            ])
            
            # Count active hosting services
            record.total_hosting = self.env['hosting.service'].search_count([
                ('status', '=', 'active')
            ])
            
            # Count unique customers with active services
            domain_customers = self.env['domain.service'].search([
                ('status', '=', 'active')
            ]).mapped('customer_id.id')
            
            hosting_customers = self.env['hosting.service'].search([
                ('status', '=', 'active')
            ]).mapped('customer_id.id')
            
            all_customers = list(set(domain_customers + hosting_customers))
            record.total_customers = len(all_customers)
            
            # Count domains expiring in the next 30 days
            record.expiring_domains = self.env['domain.service'].search_count([
                ('status', '=', 'active'),
                ('days_to_expire', '<=', 30),
                ('days_to_expire', '>', 0)
            ])
    
    @api.depends()
    def _compute_domain_provider_chart(self):
        """Compute chart data for domain providers"""
        for record in self:
            # Group domains by provider
            self.env.cr.execute("""
                SELECT domain_provider, COUNT(*) as count
                FROM domain_service
                WHERE status = 'active'
                GROUP BY domain_provider
            """)
            result = self.env.cr.fetchall()
            
            # Format data for chart
            data = {
                'labels': [r[0] for r in result],
                'datasets': [{
                    'label': 'Domains',
                    'data': [r[1] for r in result],
                    'backgroundColor': [
                        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'
                    ]
                }]
            }
            record.domain_provider_chart = json.dumps(data)
    
    @api.depends()
    def _compute_hosting_provider_chart(self):
        """Compute chart data for hosting providers"""
        for record in self:
            # Group hosting by provider
            self.env.cr.execute("""
                SELECT hosting_provider, COUNT(*) as count
                FROM hosting_service
                WHERE status = 'active'
                GROUP BY hosting_provider
            """)
            result = self.env.cr.fetchall()
            
            # Format data for chart
            data = {
                'labels': [r[0] for r in result],
                'datasets': [{
                    'label': 'Hosting',
                    'data': [r[1] for r in result],
                    'backgroundColor': [
                        '#1cc88a', '#4e73df', '#36b9cc', '#f6c23e', '#e74a3b'
                    ]
                }]
            }
            record.hosting_provider_chart = json.dumps(data)
    
    @api.depends()
    def _compute_expiring_domains_chart(self):
        """Compute chart data for expiring domains by month"""
        for record in self:
            # Get current date and next 6 months
            today = fields.Date.today()
            months = []
            for i in range(6):
                next_month = today + timedelta(days=30*i)
                months.append((next_month.year, next_month.month))
            
            # Prepare data
            labels = []
            data = []
            
            # Get count of domains expiring in each month
            for year, month in months:
                # Format label as "Month Year"
                month_name = date(year, month, 1).strftime("%B %Y")
                labels.append(month_name)
                
                # Count domains expiring in this month
                count = self.env['domain.service'].search_count([
                    ('status', '=', 'active'),
                    ('end_date', '>=', date(year, month, 1)),
                    ('end_date', '<', date(year, month+1 if month < 12 else 1, 1))
                ])
                data.append(count)
            
            # Format data for chart
            chart_data = {
                'labels': labels,
                'datasets': [{
                    'label': 'Expiring Domains',
                    'data': data,
                    'backgroundColor': '#f6c23e',
                    'borderColor': '#e74a3b',
                    'borderWidth': 1
                }]
            }
            record.expiring_domains_chart = json.dumps(chart_data)
    
    @api.depends()
    def _compute_services_by_customer_chart(self):
        """Compute chart data for services by customer"""
        for record in self:
            # Get top 10 customers by service count
            self.env.cr.execute("""
                SELECT p.name, 
                       COUNT(d.id) as domain_count, 
                       COUNT(h.id) as hosting_count
                FROM res_partner p
                LEFT JOIN domain_service d ON d.customer_id = p.id AND d.status = 'active'
                LEFT JOIN hosting_service h ON h.customer_id = p.id AND h.status = 'active'
                WHERE (d.id IS NOT NULL OR h.id IS NOT NULL)
                GROUP BY p.id, p.name
                ORDER BY (COUNT(d.id) + COUNT(h.id)) DESC
                LIMIT 10
            """)
            result = self.env.cr.fetchall()
            
            # Format data for chart
            data = {
                'labels': [r[0] for r in result],
                'datasets': [
                    {
                        'label': 'Domains',
                        'data': [r[1] for r in result],
                        'backgroundColor': '#4e73df'
                    },
                    {
                        'label': 'Hosting',
                        'data': [r[2] for r in result],
                        'backgroundColor': '#1cc88a'
                    }
                ]
            }
            record.services_by_customer_chart = json.dumps(data)