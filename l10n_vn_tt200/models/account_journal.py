# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountTax(models.Model):
    _inherit = 'account.tax'

    # Vietnamese Tax Fields
    vn_tax_type = fields.Selection([
        ('vat', 'Value Added Tax (VAT)'),
        ('import', 'Import Tax'),
        ('special', 'Special Consumption Tax'),
        ('pit', 'Personal Income Tax'),
        ('cit', 'Corporate Income Tax'),
        ('other', 'Other Tax'),
    ], string='Vietnam Tax Type', default='vat')
    
    vn_tax_code = fields.Char(
        string='Tax Code',
        help='Vietnamese tax code for reporting'
    )
    
    vn_deductible = fields.Boolean(
        string='VAT Deductible',
        default=True,
        help='Whether this VAT is deductible'
    )

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    # Vietnamese Journal Fields
    vn_journal_type = fields.Selection([
        ('cash', 'Cash Journal (Nhật ký tiền mặt)'),
        ('bank', 'Bank Journal (Nhật ký ngân hàng)'),
        ('sale', 'Sales Journal (Nhật ký bán hàng)'),
        ('purchase', 'Purchase Journal (Nhật ký mua hàng)'),
        ('general', 'General Journal (Nhật ký chung)'),
        ('fixed_asset', 'Fixed Asset Journal (Nhật ký TSCĐ)'),
    ], string='Vietnam Journal Type')
    
    vn_book_number = fields.Char(
        string='Book Number',
        help='Vietnamese accounting book number'
    )