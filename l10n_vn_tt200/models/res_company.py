# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import json
from datetime import datetime, date

class ResCompany(models.Model):
    _inherit = 'res.company'

    # Vietnamese Company Registration Fields
    vn_tax_code = fields.Char(
        string='Tax Code (MST)',
        help='Vietnamese Tax Registration Number (Mã số thuế)'
    )
    vn_business_license = fields.Char(
        string='Business License Number',
        help='Vietnamese Business Registration Certificate Number'
    )
    vn_business_license_date = fields.Date(
        string='Business License Date',
        help='Date of Business Registration Certificate'
    )
    vn_business_license_place = fields.Char(
        string='Business License Place',
        help='Place where Business License was issued'
    )
    vn_legal_representative = fields.Char(
        string='Legal Representative',
        help='Name of Legal Representative'
    )
    vn_chief_accountant = fields.Char(
        string='Chief Accountant',
        help='Name of Chief Accountant'
    )
    
    # Vietnamese Reporting Fields
    vn_fiscal_year_start = fields.Date(
        string='Fiscal Year Start',
        default=lambda self: date(date.today().year, 1, 1)
    )
    vn_accounting_method = fields.Selection([
        ('accrual', 'Accrual Method'),
        ('cash', 'Cash Method'),
    ], string='Accounting Method', default='accrual')
    
    vn_vat_declaration_period = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ], string='VAT Declaration Period', default='monthly')

class AccountAccount(models.Model):
    _inherit = 'account.account'

    # Vietnamese Account Classifications
    vn_account_nature = fields.Selection([
        ('debit', 'Debit Nature'),
        ('credit', 'Credit Nature'),
        ('both', 'Both Debit and Credit'),
    ], string='Account Nature', default='debit')
    
    vn_is_detailed = fields.Boolean(
        string='Is Detailed Account',
        help='Check if this is a detailed account (4-6 digits)'
    )
    
    vn_parent_account_id = fields.Many2one(
        'account.account',
        string='Parent Account',
        help='Parent account for hierarchical structure'
    )
    
    vn_account_level = fields.Integer(
        string='Account Level',
        compute='_compute_account_level',
        store=True
    )

    @api.depends('code')
    def _compute_account_level(self):
        for record in self:
            if record.code:
                record.vn_account_level = len(record.code.replace(' ', ''))
            else:
                record.vn_account_level = 0

class AccountMove(models.Model):
    _inherit = 'account.move'

    # Vietnamese Document Fields
    vn_document_type = fields.Selection([
        ('receipt', 'Receipt (Phiếu thu)'),
        ('payment', 'Payment (Phiếu chi)'),
        ('journal', 'Journal Entry (Bút toán)'),
        ('invoice', 'Invoice (Hóa đơn)'),
        ('credit_note', 'Credit Note (Hóa đơn điều chỉnh)'),
        ('debit_note', 'Debit Note (Thông báo nợ)'),
    ], string='Document Type', default='journal')
    
    vn_document_serial = fields.Char(
        string='Document Serial',
        help='Vietnamese Document Serial Number'
    )
    
    vn_original_currency_rate = fields.Float(
        string='Original Exchange Rate',
        help='Exchange rate at transaction date'
    )
    
    # VAT Declaration fields
    vn_vat_period = fields.Char(
        string='VAT Period',
        compute='_compute_vat_period',
        store=True
    )

    @api.depends('invoice_date', 'date')
    def _compute_vat_period(self):
        for move in self:
            invoice_date = move.invoice_date or move.date
            if invoice_date:
                # Monthly period format: YYYYMM
                move.vn_vat_period = invoice_date.strftime('%Y%m')
            else:
                move.vn_vat_period = False

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Vietnamese specific fields for journal entries
    vn_analytical_code = fields.Char(
        string='Analytical Code',
        help='Vietnamese analytical accounting code'
    )
    
    vn_foreign_currency_amount = fields.Monetary(
        string='Foreign Currency Amount',
        currency_field='currency_id'
    )

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

class VietnamVATDeclaration(models.Model):
    _name = 'vietnam.vat.declaration'
    _description = 'Vietnam VAT Declaration'
    _order = 'period_year desc, period_month desc'

    name = fields.Char(string='Declaration Name', compute='_compute_name')
    period_year = fields.Integer(string='Year', required=True)
    period_month = fields.Integer(string='Month', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    
    # VAT Declaration Lines
    sales_vat_0 = fields.Monetary(string='Sales VAT 0%', currency_field='currency_id')
    sales_vat_5 = fields.Monetary(string='Sales VAT 5%', currency_field='currency_id')
    sales_vat_10 = fields.Monetary(string='Sales VAT 10%', currency_field='currency_id')
    
    input_vat_0 = fields.Monetary(string='Input VAT 0%', currency_field='currency_id')
    input_vat_5 = fields.Monetary(string='Input VAT 5%', currency_field='currency_id')
    input_vat_10 = fields.Monetary(string='Input VAT 10%', currency_field='currency_id')
    
    vat_payable = fields.Monetary(
        string='VAT Payable',
        compute='_compute_vat_payable',
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Currency'
    )

    @api.depends('period_year', 'period_month')
    def _compute_name(self):
        for record in self:
            record.name = f"VAT Declaration {record.period_month:02d}/{record.period_year}"

    @api.depends('sales_vat_5', 'sales_vat_10', 'input_vat_5', 'input_vat_10')
    def _compute_vat_payable(self):
        for record in self:
            output_vat = (record.sales_vat_5 * 0.05) + (record.sales_vat_10 * 0.10)
            input_vat = (record.input_vat_5 * 0.05) + (record.input_vat_10 * 0.10)
            record.vat_payable = output_vat - input_vat

    def action_generate_declaration(self):
        """Generate VAT declaration data from account moves"""
        domain = [
            ('date', '>=', date(self.period_year, self.period_month, 1)),
            ('date', '<=', date(self.period_year, self.period_month, 31)),
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'posted'),
        ]
        
        moves = self.env['account.move'].search(domain)
        
        # Reset values
        self.sales_vat_0 = self.sales_vat_5 = self.sales_vat_10 = 0
        self.input_vat_0 = self.input_vat_5 = self.input_vat_10 = 0
        
        for move in moves:
            for line in move.line_ids:
                if line.tax_ids:
                    for tax in line.tax_ids:
                        if tax.vn_tax_type == 'vat' and tax.type_tax_use == 'sale':
                            if tax.amount == 0:
                                self.sales_vat_0 += abs(line.balance)
                            elif tax.amount == 5:
                                self.sales_vat_5 += abs(line.balance)
                            elif tax.amount == 10:
                                self.sales_vat_10 += abs(line.balance)
                        elif tax.vn_tax_type == 'vat' and tax.type_tax_use == 'purchase':
                            if tax.amount == 0:
                                self.input_vat_0 += abs(line.balance)
                            elif tax.amount == 5:
                                self.input_vat_5 += abs(line.balance)
                            elif tax.amount == 10:
                                self.input_vat_10 += abs(line.balance)