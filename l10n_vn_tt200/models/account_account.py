# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

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

    def _get_balance(self, date_from=None, date_to=None):
        """Get account balance for the specified period"""
        self.ensure_one()
        domain = [('account_id', '=', self.id), ('parent_state', '=', 'posted')]
        
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
            
        move_lines = self.env['account.move.line'].search(domain)
        return sum(move_lines.mapped('balance'))