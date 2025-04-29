{
    'name': 'BOM Bulk Product Publish',
    'version': '16.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Bulk publish unpublished products with one click',
    'description': 'This module allows users to publish all unpublished products with a single click.',
    'author': 'BOM Communications',
    'website': 'https://bom.asia',
    'depends': ['product', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bom_bulk_product_publish/static/src/js/bulk_publish.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
}