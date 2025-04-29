from odoo import http
from odoo.http import request
import json


class BomBulkPublishController(http.Controller):
    
    @http.route('/bom_bulk_product_publish/publish_direct', type='json', auth='user')
    def publish_direct(self, product_ids=None):
        """
        Controller method to directly publish selected products using SQL
        to avoid singleton errors with the write method
        
        Args:
            product_ids: List of product IDs to publish
        """
        if not product_ids:
            return {'success': False, 'message': 'No products selected'}
        
        try:
            # Convert to tuple for SQL IN clause
            product_ids_tuple = tuple(product_ids)
            
            # Use direct SQL query to update records
            query = """
                UPDATE product_template 
                SET is_published = TRUE 
                WHERE id IN %s
                RETURNING id
            """
            request.env.cr.execute(query, (product_ids_tuple,))
            
            # Get the updated records
            updated_records = request.env.cr.fetchall()
            count = len(updated_records)
            
            # Clear the cache to ensure UI update
            request.env['product.template'].clear_caches()
            
            return {
                'success': True,
                'count': count,
                'message': f'{count} products published successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }