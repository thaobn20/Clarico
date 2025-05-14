{
    'name': 'BOM Custom Document Templates',
    'version': '1.0',
    'category': 'Sales/Sales',
    'summary': 'Custom templates for quotations, invoices, POs and delivery slips',
    'description': """
BOM Custom Document Templates
==========================
This module customizes the default templates for:
- Quotations and Sale Orders
- Invoices
- Purchase Orders
- Delivery Slips

It includes company logo placement and styling for professional documents.
    """,
    'author': 'BOM Communications',
    'website': 'https://bom.asia',
    'maintainer': 'Thao Bui',
    'support': 'support@bom.asia',
    'depends': [
        'account',
        'sale_management',
        'purchase',
        'stock',
    ],
    'data': [
        'data/paper_format.xml',
        'views/res_company_views.xml',
        'reports/report_styles.xml',
        'reports/sale_order_report.xml',
        'reports/invoice_report.xml',
        'reports/purchase_order_report.xml',
        #'reports/stock_report.xml',
        'reports/delivery_report.xml',
        'reports/stock_receipt_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}