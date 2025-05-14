from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    report_logo = fields.Binary(string='Report Logo', help='Logo to display on reports. If not set, the company logo will be used.')
    report_bank_name = fields.Char(string='Bank Name', help='Bank name to display on reports')
    report_bank_address = fields.Text(string='Bank Address', help='Bank address to display on reports')
    report_swift_code = fields.Char(string='Swift Code', help='Swift code to display on reports')
    report_account_number = fields.Char(string='Account Number', help='Account number to display on reports')
    report_contact_person = fields.Char(string='Contact Person', help='Contact person to display on reports')
    report_contact_phone = fields.Char(string='Contact Phone', help='Contact phone to display on reports')
    report_contact_email = fields.Char(string='Contact Email', help='Contact email to display on reports')
    report_note = fields.Text(string='Report Note', help='Note to display on reports')