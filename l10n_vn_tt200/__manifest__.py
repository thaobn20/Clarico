# -*- coding: utf-8 -*-
{
    'name': 'Vietnam Accounting TT200/2014',
    'version': '15.0.1.0.0',
    'category': 'Localization',
    'summary': 'Vietnamese Accounting Standards (Circular 200/2014/TT-BTC)',
    'description': """
Vietnam Accounting Standards (TT200/2014)
==========================================

This module provides:
* Vietnamese Chart of Accounts according to Circular 200/2014/TT-BTC
* Financial Reports (B01-DN, B02-DN, B03-DN)
* VAT declarations and compliance with 0%, 5%, 8%, 10% rates
* Bank and cash management according to Vietnamese standards
* Multi-currency support with VND as base currency

Key Features:
* Complete chart of accounts with 4-level structure
* Automatic journal entries for Vietnamese transactions
* VAT reporting and declarations (including 8% VAT)
* Financial statements in Vietnamese format
* Trial balance and cash flow statements
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Data files
        'data/account_chart_template.xml',
        'data/account_tax_template.xml',
        
        # Views
        'views/res_company_views.xml',
        'views/account_views.xml',
        'views/vietnam_views.xml',
        
        # Reports
        'reports/report_balance_sheet_b01.xml',
        'reports/report_income_statement_b02.xml',
        'reports/report_cash_flow_b03.xml',
        'reports/report_trial_balance.xml',
        'reports/report_vat_declaration.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': ['openpyxl', 'xlsxwriter'],
    },
}