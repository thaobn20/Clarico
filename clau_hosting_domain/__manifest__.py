{
    'name': 'Hosting & Domain Management',
    'version': '15.0.1.1',
    'summary': 'Manage hosting and domain services',
    'description': """
        This module allows you to manage hosting and domain services offered to customers.  
        It includes tracking of service periods, vendors, domain types, and renewal status.
        Features a dashboard to monitor key metrics like service count, customer count, and expiration trends.
    """,
    'category': 'Services/Hosting',
    'author': 'BOM Communications',
    'website': 'https://www.bom.asia',
    'depends': ['base', 'mail', 'web', 'sale'],  # Add 'sale' to dependencies
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
       'views/hosting_views.xml',
        'views/domain_views.xml',
        'views/extension_views.xml',
        'views/dashboard_views.xml',
        'views/sale_order_view.xml',
        'views/so_dashboard_views.xml',
        'views/menu.xml',
        'data/cron.xml',
        'data/email_templates.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'clau_hosting_domain/static/src/js/dashboard.js',
            'clau_hosting_domain/static/src/css/dashboard.css',
        ],
    },
    'license': 'LGPL-3',
}