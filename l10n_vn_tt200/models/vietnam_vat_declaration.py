# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date

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
    sales_vat_8 = fields.Monetary(string='Sales VAT 8%', currency_field='currency_id')
    sales_vat_10 = fields.Monetary(string='Sales VAT 10%', currency_field='currency_id')
    
    input_vat_0 = fields.Monetary(string='Input VAT 0%', currency_field='currency_id')
    input_vat_5 = fields.Monetary(string='Input VAT 5%', currency_field='currency_id')
    input_vat_8 = fields.Monetary(string='Input VAT 8%', currency_field='currency_id')
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

    @api.depends('sales_vat_5', 'sales_vat_8', 'sales_vat_10', 'input_vat_5', 'input_vat_8', 'input_vat_10')
    def _compute_vat_payable(self):
        for record in self:
            output_vat = (record.sales_vat_5 * 0.05) + (record.sales_vat_8 * 0.08) + (record.sales_vat_10 * 0.10)
            input_vat = (record.input_vat_5 * 0.05) + (record.input_vat_8 * 0.08) + (record.input_vat_10 * 0.10)
            record.vat_payable = output_vat - input_vat

    def action_generate_declaration(self):
        """Generate VAT declaration data from account moves"""
        domain = [
            ('date', '>=', date(self.period_year, self.period_month, 1)),
            ('date', '<=', self._get_month_end_date()),
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'posted'),
        ]
        
        moves = self.env['account.move'].search(domain)
        
        # Reset values
        self.sales_vat_0 = self.sales_vat_5 = self.sales_vat_8 = self.sales_vat_10 = 0
        self.input_vat_0 = self.input_vat_5 = self.input_vat_8 = self.input_vat_10 = 0
        
        for move in moves:
            for line in move.line_ids:
                if line.tax_ids:
                    for tax in line.tax_ids:
                        if tax.vn_tax_type == 'vat' and tax.type_tax_use == 'sale':
                            if tax.amount == 0:
                                self.sales_vat_0 += abs(line.balance)
                            elif tax.amount == 5:
                                self.sales_vat_5 += abs(line.balance)
                            elif tax.amount == 8:
                                self.sales_vat_8 += abs(line.balance)
                            elif tax.amount == 10:
                                self.sales_vat_10 += abs(line.balance)
                        elif tax.vn_tax_type == 'vat' and tax.type_tax_use == 'purchase':
                            if tax.amount == 0:
                                self.input_vat_0 += abs(line.balance)
                            elif tax.amount == 5:
                                self.input_vat_5 += abs(line.balance)
                            elif tax.amount == 8:
                                self.input_vat_8 += abs(line.balance)
                            elif tax.amount == 10:
                                self.input_vat_10 += abs(line.balance)

    def _get_month_end_date(self):
        """Get the last day of the period month"""
        if self.period_month == 12:
            return date(self.period_year + 1, 1, 1) - date.timedelta(days=1)
        else:
            return date(self.period_year, self.period_month + 1, 1) - date.timedelta(days=1)

    @api.constrains('period_month')
    def _check_period_month(self):
        for record in self:
            if not (1 <= record.period_month <= 12):
                raise ValidationError(_('Month must be between 1 and 12'))