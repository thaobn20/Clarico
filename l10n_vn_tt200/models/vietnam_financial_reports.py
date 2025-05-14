# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, date
import json

class VietnamFinancialReport(models.Model):
    _name = 'vietnam.financial.report'
    _description = 'Vietnam Financial Report'

    name = fields.Char(string='Report Name', required=True)
    report_type = fields.Selection([
        ('b01', 'Balance Sheet (B01-DN)'),
        ('b02', 'Income Statement (B02-DN)'),
        ('b03', 'Cash Flow Statement (B03-DN)'),
    ], string='Report Type', required=True)
    
    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    
    # Report data stored as JSON
    report_data = fields.Text(string='Report Data')

class VietnamBalanceSheet(models.Model):
    _name = 'vietnam.balance.sheet'
    _description = 'Vietnam Balance Sheet (B01-DN)'
    _auto = False

    @api.model
    def get_balance_sheet_data(self, date_from, date_to, company_id):
        """Generate Vietnamese Balance Sheet according to B01-DN format"""
        
        # Assets Section
        assets_data = {
            # A. CURRENT ASSETS
            'current_assets': {
                '100': {'name': 'I. Cash and cash equivalents', 'value': 0},
                '110': {'name': '1. Cash', 'value': 0},
                '111': {'name': '2. Cash equivalents', 'value': 0},
                '120': {'name': 'II. Short-term financial investments', 'value': 0},
                '130': {'name': 'III. Short-term accounts receivable', 'value': 0},
                '131': {'name': '1. Trade receivables', 'value': 0},
                '132': {'name': '2. Prepayments to suppliers', 'value': 0},
                '133': {'name': '3. Receivables from employees', 'value': 0},
                '134': {'name': '4. Receivables from government budget', 'value': 0},
                '135': {'name': '5. Other short-term receivables', 'value': 0},
                '140': {'name': '6. Provision for bad debts', 'value': 0},
                '150': {'name': 'IV. Inventories', 'value': 0},
                '151': {'name': '1. Raw materials and supplies', 'value': 0},
                '152': {'name': '2. Work in progress', 'value': 0},
                '153': {'name': '3. Finished goods', 'value': 0},
                '154': {'name': '4. Merchandise inventories', 'value': 0},
                '155': {'name': '5. Inventory in transit', 'value': 0},
                '160': {'name': 'V. Other current assets', 'value': 0},
                '161': {'name': '1. Short-term prepaid expenses', 'value': 0},
                '162': {'name': '2. VAT deductible', 'value': 0},
                '163': {'name': '3. Taxes and other receivables from government', 'value': 0},
                '200': {'name': 'TOTAL CURRENT ASSETS', 'value': 0},
            },
            
            # B. LONG-TERM ASSETS
            'long_term_assets': {
                '210': {'name': 'I. Long-term receivables', 'value': 0},
                '220': {'name': 'II. Fixed assets', 'value': 0},
                '221': {'name': '1. Tangible fixed assets', 'value': 0},
                '222': {'name': '   - Original cost', 'value': 0},
                '223': {'name': '   - Accumulated depreciation', 'value': 0},
                '224': {'name': '2. Finance lease fixed assets', 'value': 0},
                '225': {'name': '   - Original cost', 'value': 0},
                '226': {'name': '   - Accumulated depreciation', 'value': 0},
                '227': {'name': '3. Intangible fixed assets', 'value': 0},
                '228': {'name': '   - Original cost', 'value': 0},
                '229': {'name': '   - Accumulated amortization', 'value': 0},
                '230': {'name': 'III. Investment property', 'value': 0},
                '240': {'name': 'IV. Long-term assets in progress', 'value': 0},
                '250': {'name': 'V. Long-term financial investments', 'value': 0},
                '260': {'name': 'VI. Other long-term assets', 'value': 0},
                '270': {'name': 'TOTAL LONG-TERM ASSETS', 'value': 0},
            },
            
            'total_assets': {'name': 'TOTAL ASSETS', 'value': 0}
        }
        
        # Liabilities and Equity Section
        liabilities_equity_data = {
            # C. DEBT
            'debt': {
                '300': {'name': 'I. Short-term liabilities', 'value': 0},
                '310': {'name': '1. Trade payables', 'value': 0},
                '311': {'name': '2. Advances from customers', 'value': 0},
                '312': {'name': '3. Taxes and other payables to government', 'value': 0},
                '313': {'name': '4. Accrued expenses', 'value': 0},
                '314': {'name': '5. Short-term unearned revenue', 'value': 0},
                '315': {'name': '6. Other short-term liabilities', 'value': 0},
                '320': {'name': '7. Short-term borrowings', 'value': 0},
                '330': {'name': 'II. Long-term liabilities', 'value': 0},
                '331': {'name': '1. Long-term borrowings', 'value': 0},
                '332': {'name': '2. Long-term unearned revenue', 'value': 0},
                '333': {'name': '3. Other long-term liabilities', 'value': 0},
                '400': {'name': 'TOTAL DEBT', 'value': 0},
            },
            
            # D. OWNER'S EQUITY
            'equity': {
                '410': {'name': 'I. Owner\'s equity', 'value': 0},
                '411': {'name': '1. Share capital', 'value': 0},
                '412': {'name': '2. Capital surplus', 'value': 0},
                '413': {'name': '3. Treasury shares', 'value': 0},
                '414': {'name': '4. Other equity', 'value': 0},
                '415': {'name': '5. Retained earnings', 'value': 0},
                '416': {'name': '   - Retained earnings to date', 'value': 0},
                '417': {'name': '   - Current year earnings', 'value': 0},
                '420': {'name': 'II. Non-controlling interests', 'value': 0},
                '440': {'name': 'TOTAL OWNER\'S EQUITY', 'value': 0},
            },
            
            'total_liabilities_equity': {'name': 'TOTAL LIABILITIES AND OWNER\'S EQUITY', 'value': 0}
        }
        
        # Calculate actual values from accounting data
        self._compute_balance_sheet_values(assets_data, liabilities_equity_data, date_to, company_id)
        
        return {
            'assets': assets_data,
            'liabilities_equity': liabilities_equity_data,
            'date': date_to,
            'company': self.env['res.company'].browse(company_id)
        }

    def _compute_balance_sheet_values(self, assets_data, liabilities_equity_data, date_to, company_id):
        """Compute actual values for balance sheet"""
        
        # Get account balances
        account_obj = self.env['account.account']
        
        # Current Assets
        # Cash and Bank
        cash_accounts = account_obj.search([
            ('code', '=like', '111%'),
            ('company_id', '=', company_id)
        ])
        cash_total = sum(acc._get_balance(date_to) for acc in cash_accounts)
        assets_data['current_assets']['110']['value'] = cash_total
        
        bank_accounts = account_obj.search([
            ('code', '=like', '112%'),
            ('company_id', '=', company_id)
        ])
        bank_total = sum(acc._get_balance(date_to) for acc in bank_accounts)
        assets_data['current_assets']['111']['value'] = bank_total
        assets_data['current_assets']['100']['value'] = cash_total + bank_total
        
        # Accounts Receivable
        receivable_accounts = account_obj.search([
            ('code', '=like', '131%'),
            ('company_id', '=', company_id)
        ])
        receivable_total = sum(acc._get_balance(date_to) for acc in receivable_accounts)
        assets_data['current_assets']['131']['value'] = receivable_total
        assets_data['current_assets']['130']['value'] = receivable_total
        
        # Inventory
        inventory_accounts = account_obj.search([
            ('code', '=like', '15%'),
            ('company_id', '=', company_id)
        ])
        inventory_total = sum(acc._get_balance(date_to) for acc in inventory_accounts)
        assets_data['current_assets']['150']['value'] = inventory_total
        
        # Total Current Assets
        assets_data['current_assets']['200']['value'] = (
            assets_data['current_assets']['100']['value'] +
            assets_data['current_assets']['130']['value'] +
            assets_data['current_assets']['150']['value']
        )
        
        # Fixed Assets
        fixed_asset_accounts = account_obj.search([
            ('code', '=like', '211%'),
            ('company_id', '=', company_id)
        ])
        fixed_asset_total = sum(acc._get_balance(date_to) for acc in fixed_asset_accounts)
        assets_data['long_term_assets']['222']['value'] = fixed_asset_total
        
        depreciation_accounts = account_obj.search([
            ('code', '=like', '214%'),
            ('company_id', '=', company_id)
        ])
        depreciation_total = sum(acc._get_balance(date_to) for acc in depreciation_accounts)
        assets_data['long_term_assets']['223']['value'] = -depreciation_total
        assets_data['long_term_assets']['221']['value'] = fixed_asset_total - depreciation_total
        
        # Total Long-term Assets
        assets_data['long_term_assets']['270']['value'] = assets_data['long_term_assets']['221']['value']
        
        # Total Assets
        assets_data['total_assets']['value'] = (
            assets_data['current_assets']['200']['value'] +
            assets_data['long_term_assets']['270']['value']
        )
        
        # Liabilities
        # Accounts Payable
        payable_accounts = account_obj.search([
            ('code', '=like', '331%'),
            ('company_id', '=', company_id)
        ])
        payable_total = sum(acc._get_balance(date_to) for acc in payable_accounts)
        liabilities_equity_data['debt']['310']['value'] = -payable_total
        
        # VAT Payable
        vat_payable_accounts = account_obj.search([
            ('code', '=like', '3333%'),
            ('company_id', '=', company_id)
        ])
        vat_payable_total = sum(acc._get_balance(date_to) for acc in vat_payable_accounts)
        liabilities_equity_data['debt']['312']['value'] = -vat_payable_total
        
        # Total Short-term Liabilities
        liabilities_equity_data['debt']['300']['value'] = (
            liabilities_equity_data['debt']['310']['value'] +
            liabilities_equity_data['debt']['312']['value']
        )
        
        # Total Debt
        liabilities_equity_data['debt']['400']['value'] = liabilities_equity_data['debt']['300']['value']
        
        # Equity
        # Share Capital
        equity_accounts = account_obj.search([
            ('code', '=like', '411%'),
            ('company_id', '=', company_id)
        ])
        equity_total = sum(acc._get_balance(date_to) for acc in equity_accounts)
        liabilities_equity_data['equity']['411']['value'] = -equity_total
        
        # Retained Earnings
        retained_accounts = account_obj.search([
            ('code', '=like', '421%'),
            ('company_id', '=', company_id)
        ])
        retained_total = sum(acc._get_balance(date_to) for acc in retained_accounts)
        liabilities_equity_data['equity']['416']['value'] = -retained_total
        
        # Total Equity
        liabilities_equity_data['equity']['440']['value'] = (
            liabilities_equity_data['equity']['411']['value'] +
            liabilities_equity_data['equity']['416']['value']
        )
        
        # Total Liabilities and Equity
        liabilities_equity_data['total_liabilities_equity']['value'] = (
            liabilities_equity_data['debt']['400']['value'] +
            liabilities_equity_data['equity']['440']['value']
        )

class VietnamIncomeStatement(models.Model):
    _name = 'vietnam.income.statement'
    _description = 'Vietnam Income Statement (B02-DN)'
    _auto = False

    @api.model
    def get_income_statement_data(self, date_from, date_to, company_id):
        """Generate Vietnamese Income Statement according to B02-DN format"""
        
        income_statement_data = {
            # 1. REVENUE
            'revenue': {
                '01': {'name': '1. Revenue from sales of goods and services', 'value': 0},
                '02': {'name': '2. Deductions from revenue', 'value': 0},
                '10': {'name': '3. Net revenue from sales of goods and services (10 = 01 - 02)', 'value': 0},
                '11': {'name': '4. Cost of goods sold', 'value': 0},
                '20': {'name': '5. Gross profit from sales of goods and services (20 = 10 - 11)', 'value': 0},
            },
            
            # 2. FINANCIAL ACTIVITIES
            'financial': {
                '21': {'name': '6. Financial income', 'value': 0},
                '22': {'name': '7. Financial expenses', 'value': 0},
                '23': {'name': '   - Interest expenses', 'value': 0},
                '24': {'name': '   - Foreign exchange losses', 'value': 0},
                '25': {'name': '   - Other financial expenses', 'value': 0},
                '30': {'name': '8. Net financial income (30 = 21 - 22)', 'value': 0},
            },
            
            # 3. OPERATING ACTIVITIES
            'operating': {
                '31': {'name': '9. Selling expenses', 'value': 0},
                '32': {'name': '10. General and administrative expenses', 'value': 0},
                '40': {'name': '11. Operating profit (40 = 20 + 30 - 31 - 32)', 'value': 0},
                '41': {'name': '12. Other income', 'value': 0},
                '42': {'name': '13. Other expenses', 'value': 0},
                '43': {'name': '14. Other profit (43 = 41 - 42)', 'value': 0},
                '50': {'name': '15. Accounting profit before tax (50 = 40 + 43)', 'value': 0},
                '51': {'name': '16. Corporate income tax expense', 'value': 0},
                '60': {'name': '17. Profit after corporate income tax (60 = 50 - 51)', 'value': 0},
            },
            
            # 4. OTHER COMPREHENSIVE INCOME
            'comprehensive': {
                '61': {'name': '18. Other comprehensive income', 'value': 0},
                '70': {'name': '19. Total comprehensive income (70 = 60 + 61)', 'value': 0},
            },
            
            # 5. EARNINGS PER SHARE
            'eps': {
                '71': {'name': '20. Basic earnings per share', 'value': 0},
                '72': {'name': '21. Diluted earnings per share', 'value': 0},
            }
        }
        
        # Calculate actual values
        self._compute_income_statement_values(income_statement_data, date_from, date_to, company_id)
        
        return {
            'data': income_statement_data,
            'date_from': date_from,
            'date_to': date_to,
            'company': self.env['res.company'].browse(company_id)
        }

    def _compute_income_statement_values(self, data, date_from, date_to, company_id):
        """Compute actual values for income statement"""
        
        account_obj = self.env['account.account']
        
        # Revenue from Sales
        revenue_accounts = account_obj.search([
            ('code', '=like', '511%'),
            ('company_id', '=', company_id)
        ])
        revenue_total = -sum(acc._get_balance(date_from, date_to) for acc in revenue_accounts)
        data['revenue']['01']['value'] = revenue_total
        data['revenue']['10']['value'] = revenue_total
        
        # Cost of Goods Sold
        cogs_accounts = account_obj.search([
            ('code', '=like', '621%'),
            ('company_id', '=', company_id)
        ])
        cogs_total = sum(acc._get_balance(date_from, date_to) for acc in cogs_accounts)
        data['revenue']['11']['value'] = cogs_total
        
        # Gross Profit
        data['revenue']['20']['value'] = data['revenue']['10']['value'] - data['revenue']['11']['value']
        
        # Operating Expenses
        selling_accounts = account_obj.search([
            ('code', '=like', '642%'),
            ('company_id', '=', company_id)
        ])
        selling_total = sum(acc._get_balance(date_from, date_to) for acc in selling_accounts)
        data['operating']['31']['value'] = selling_total
        
        admin_accounts = account_obj.search([
            ('code', '=like', '641%'),
            ('company_id', '=', company_id)
        ])
        admin_total = sum(acc._get_balance(date_from, date_to) for acc in admin_accounts)
        data['operating']['32']['value'] = admin_total
        
        # Financial Income/Expenses
        financial_income_accounts = account_obj.search([
            ('code', '=like', '515%'),
            ('company_id', '=', company_id)
        ])
        financial_income_total = -sum(acc._get_balance(date_from, date_to) for acc in financial_income_accounts)
        data['financial']['21']['value'] = financial_income_total
        
        financial_expense_accounts = account_obj.search([
            ('code', '=like', '635%'),
            ('company_id', '=', company_id)
        ])
        financial_expense_total = sum(acc._get_balance(date_from, date_to) for acc in financial_expense_accounts)
        data['financial']['22']['value'] = financial_expense_total
        data['financial']['30']['value'] = data['financial']['21']['value'] - data['financial']['22']['value']
        
        # Operating Profit
        data['operating']['40']['value'] = (
            data['revenue']['20']['value'] +
            data['financial']['30']['value'] -
            data['operating']['31']['value'] -
            data['operating']['32']['value']
        )
        
        # Profit before tax
        data['operating']['50']['value'] = data['operating']['40']['value'] + data['operating']['43']['value']
        
        # Profit after tax
        data['operating']['60']['value'] = data['operating']['50']['value'] - data['operating']['51']['value']
        
        # Total comprehensive income
        data['comprehensive']['70']['value'] = data['operating']['60']['value'] + data['comprehensive']['61']['value']

class VietnamCashFlowStatement(models.Model):
    _name = 'vietnam.cash.flow.statement'
    _description = 'Vietnam Cash Flow Statement (B03-DN)'
    _auto = False

    @api.model
    def get_cash_flow_data(self, date_from, date_to, company_id):
        """Generate Vietnamese Cash Flow Statement according to B03-DN format"""
        
        cash_flow_data = {
            # I. CASH FLOWS FROM OPERATING ACTIVITIES
            'operating': {
                '01': {'name': '1. Profit before tax', 'value': 0},
                '02': {'name': '2. Adjustments for:', 'value': 0},
                '03': {'name': '   - Depreciation and amortization', 'value': 0},
                '04': {'name': '   - Provisions', 'value': 0},
                '05': {'name': '   - Foreign exchange losses (gains)', 'value': 0},
                '06': {'name': '   - Loss (gain) on disposal of fixed assets', 'value': 0},
                '07': {'name': '   - Interest expense', 'value': 0},
                '08': {'name': '   - Interest income', 'value': 0},
                '09': {'name': '   - Other adjustments', 'value': 0},
                '10': {'name': '3. Operating profit before changes in working capital', 'value': 0},
                '11': {'name': '4. Changes in receivables', 'value': 0},
                '12': {'name': '5. Changes in inventories', 'value': 0},
                '13': {'name': '6. Changes in payables', 'value': 0},
                '14': {'name': '7. Changes in prepaid expenses', 'value': 0},
                '15': {'name': '8. Interest paid', 'value': 0},
                '16': {'name': '9. Corporate income tax paid', 'value': 0},
                '17': {'name': '10. Other receipts from operating activities', 'value': 0},
                '18': {'name': '11. Other payments for operating activities', 'value': 0},
                '20': {'name': 'Net cash flows from operating activities', 'value': 0},
            },
            
            # II. CASH FLOWS FROM INVESTING ACTIVITIES
            'investing': {
                '21': {'name': '1. Purchase of fixed assets and other long-term assets', 'value': 0},
                '22': {'name': '2. Proceeds from disposal of fixed assets and other long-term assets', 'value': 0},
                '23': {'name': '3. Loans made to other entities', 'value': 0},
                '24': {'name': '4. Collection of loans from other entities', 'value': 0},
                '25': {'name': '5. Interest received', 'value': 0},
                '26': {'name': '6. Dividends and other investment income received', 'value': 0},
                '27': {'name': '7. Other receipts from investing activities', 'value': 0},
                '28': {'name': '8. Other payments for investing activities', 'value': 0},
                '30': {'name': 'Net cash flows from investing activities', 'value': 0},
            },
            
            # III. CASH FLOWS FROM FINANCING ACTIVITIES
            'financing': {
                '31': {'name': '1. Proceeds from issuance of shares', 'value': 0},
                '32': {'name': '2. Proceeds from borrowings', 'value': 0},
                '33': {'name': '3. Repayment of borrowings', 'value': 0},
                '34': {'name': '4. Dividends paid', 'value': 0},
                '35': {'name': '5. Other receipts from financing activities', 'value': 0},
                '36': {'name': '6. Other payments for financing activities', 'value': 0},
                '40': {'name': 'Net cash flows from financing activities', 'value': 0},
            },
            
            # SUMMARY
            'summary': {
                '50': {'name': 'Net increase (decrease) in cash and cash equivalents (50 = 20 + 30 + 40)', 'value': 0},
                '60': {'name': 'Cash and cash equivalents at beginning of period', 'value': 0},
                '61': {'name': 'Effect of exchange rate fluctuations', 'value': 0},
                '70': {'name': 'Cash and cash equivalents at end of period (70 = 50 + 60 + 61)', 'value': 0},
            }
        }
        
        # Calculate actual values
        self._compute_cash_flow_values(cash_flow_data, date_from, date_to, company_id)
        
        return {
            'data': cash_flow_data,
            'date_from': date_from,
            'date_to': date_to,
            'company': self.env['res.company'].browse(company_id)
        }

    def _compute_cash_flow_values(self, data, date_from, date_to, company_id):
        """Compute actual values for cash flow statement"""
        
        account_obj = self.env['account.account']
        
        # Get profit before tax from income statement
        income_stmt = self.env['vietnam.income.statement']
        income_data = income_stmt.get_income_statement_data(date_from, date_to, company_id)
        data['operating']['01']['value'] = income_data['data']['operating']['50']['value']
        
        # Depreciation
        depre_accounts = account_obj.search([
            ('code', '=like', '214%'),
            ('company_id', '=', company_id)
        ])
        depre_total = sum(acc._get_balance(date_from, date_to) for acc in depre_accounts)
        data['operating']['03']['value'] = depre_total
        
        # Operating profit before working capital changes
        data['operating']['10']['value'] = (
            data['operating']['01']['value'] +
            data['operating']['03']['value']
        )
        
        # Changes in working capital (simplified calculation)
        # This would need more sophisticated logic for accurate working capital changes
        
        # Cash and cash equivalents
        cash_accounts = account_obj.search([
            ('code', '=like', '111%'),
            ('code', '=like', '112%'),
            ('company_id', '=', company_id)
        ])
        
        # Beginning cash
        cash_beginning = sum(acc._get_balance(date_from) for acc in cash_accounts)
        data['summary']['60']['value'] = cash_beginning
        
        # Ending cash
        cash_ending = sum(acc._get_balance(date_to) for acc in cash_accounts)
        data['summary']['70']['value'] = cash_ending
        
        # Net increase/decrease
        data['summary']['50']['value'] = cash_ending - cash_beginning

class VietnamTrialBalance(models.Model):
    _name = 'vietnam.trial.balance'
    _description = 'Vietnam Trial Balance'
    _auto = False

    @api.model
    def get_trial_balance_data(self, date_from, date_to, company_id):
        """Generate Trial Balance in Vietnamese format"""
        
        account_obj = self.env['account.account']
        accounts = account_obj.search([
            ('company_id', '=', company_id),
            ('deprecated', '=', False)
        ], order='code')
        
        trial_balance_data = []
        
        for account in accounts:
            # Get opening balance
            opening_balance = account._get_balance(date_from)
            opening_debit = opening_balance if opening_balance > 0 else 0
            opening_credit = -opening_balance if opening_balance < 0 else 0
            
            # Get period movements
            period_balance = account._get_balance(date_from, date_to)
            period_debit = period_balance if period_balance > 0 else 0
            period_credit = -period_balance if period_balance < 0 else 0
            
            # Get closing balance
            closing_balance = account._get_balance(date_to)
            closing_debit = closing_balance if closing_balance > 0 else 0
            closing_credit = -closing_balance if closing_balance < 0 else 0
            
            trial_balance_data.append({
                'account_code': account.code,
                'account_name': account.name,
                'opening_debit': opening_debit,
                'opening_credit': opening_credit,
                'period_debit': period_debit,
                'period_credit': period_credit,
                'closing_debit': closing_debit,
                'closing_credit': closing_credit,
            })
        
        return {
            'data': trial_balance_data,
            'date_from': date_from,
            'date_to': date_to,
            'company': self.env['res.company'].browse(company_id)
        }