# -*- coding: utf-8 -*-
{
    'name': 'BNT: Templates',
    'version': '15.0.1',
    'author': 'Timmy Nguyen',
    'summary': 'Mail',
    'website': '',
    'description': """Module help manager Mail (PO/SO)""",
    'depends': [
        'purchase',
        'sale',
        'stock',
        'account',
    ],
    'data': [
        #'views/header_templates.xml',
        'views/sale_order_template.xml',
        'views/rfq_template_views.xml',
        'views/purchase_order_template.xml',
        'views/invoice_template.xml',
        'views/pro_forma_invoice_templates.xml',
        'views/pnk_template.xml',
        'views/pxk_template.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': True,
}
