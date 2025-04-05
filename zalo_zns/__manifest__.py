{
    'name': 'Zalo ZNS Integration',
    'version': '1.0',
    'category': 'Sales/CRM',
    'summary': 'Integrate Zalo Notification Service (ZNS) with Odoo',
    'description': """
Zalo ZNS Integration
===================
This module integrates Odoo with Zalo Notification Service (ZNS) to send 
notifications for various business events like Sales Orders, Purchase Orders, 
Invoices, etc.

Features:
- Connect and manage Zalo ZNS templates
- Send notifications for Sales Orders
- Send notifications for Purchase Orders
- Send notifications for Invoices
- Dashboard for notification reporting
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'sale_management',
        'purchase',
        'account',
        'web',
    ],
    'data': [
            'security/zns_security.xml',
            'security/ir.model.access.csv',
            # Base views first
            'views/zns_config_views.xml',
            'views/zns_template_views.xml',
            'views/zns_history_views.xml',
            'views/sale_order_views.xml',
            'views/purchase_order_views.xml',
            'views/account_move_views.xml',
            'views/dashboard_views.xml',
            'views/menu_views.xml',
            # Debug views after base views
            'views/zns_config_views_debug.xml',
            'wizard/zns_test_wizard_views.xml',
            'wizard/zns_debug_wizards_views.xml',
            'wizards/zns_template_wizard_views.xml',  # Add this line
            'data/default_templates.xml',
            'data/cron_jobs.xml',
            
    ],
    'assets': {
        'web.assets_backend': [
            'zalo_zns/static/src/js/dashboard.js',
            'zalo_zns/static/src/scss/dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}