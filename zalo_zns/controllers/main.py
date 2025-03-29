from odoo import http, _
from odoo.http import request

class ZaloZNSController(http.Controller):
    @http.route('/zalo_zns/webhook', type='json', auth='public')
    def zns_webhook(self, **kwargs):
        """
        Webhook to receive status updates from Zalo ZNS
        """
        # Extract data from the request
        data = request.jsonrequest
        
        if not data:
            return {'success': False, 'message': 'No data received'}
            
        message_id = data.get('message_id')
        status = data.get('status')
        
        if not message_id or not status:
            return {'success': False, 'message': 'Missing required fields'}
            
        # Update message status in the database
        history = request.env['zalo.zns.history'].sudo().search([
            ('zns_message_id', '=', message_id)
        ], limit=1)
        
        if not history:
            return {'success': False, 'message': 'Message not found'}
            
        # Map status values
        status_mapping = {
            'DELIVERED': 'delivered',
            'FAILED': 'failed',
            'SENT': 'sent',
            'PENDING': 'pending',
        }
        
        odoo_status = status_mapping.get(status.upper(), 'pending')
        error_message = data.get('error_message', '')
        
        # Update the history record
        history.write({
            'status': odoo_status,
            'error_message': error_message if odoo_status == 'failed' else False,
        })
        
        return {'success': True, 'message': 'Status updated successfully'}