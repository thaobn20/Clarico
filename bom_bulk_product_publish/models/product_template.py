from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    def publish_selected_products(self):
        """Publish only the selected products using direct SQL to bypass write method"""
        if not self:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Products Selected'),
                    'message': _('Please select at least one product to publish.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        try:
            # Get the IDs of selected products
            product_ids = tuple(self.ids)
            
            # Use direct SQL to update only the selected products
            # This bypasses the write method that causes singleton errors
            self.env.cr.execute("""
                UPDATE product_template 
                SET is_published = TRUE 
                WHERE id IN %s
            """, (product_ids,))
            
            # Invalidate cache to ensure UI reflects changes
            self.invalidate_cache()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('%s products have been published successfully!') % len(product_ids),
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            raise UserError(_("Error while publishing products: %s") % str(e))