# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

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