odoo.define('bom_bulk_product_publish.bulk_publish', function (require) {
    "use strict";
    
    var core = require('web.core');
    var ListController = require('web.ListController');
    var _t = core._t;
    
    // Add a button to the list view toolbar
    ListController.include({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.modelName === 'product.template') {
                if (this.$buttons) {
                    var $bulkPublishButton = $('<button/>', {
                        text: _t('Publish Selected Products'),
                        class: 'btn btn-primary o_list_button_bulk_publish',
                    });
                    
                    this.$buttons.append($bulkPublishButton);
                    $bulkPublishButton.on('click', this._onBulkPublishClick.bind(this));
                }
            }
        },
        
        _onBulkPublishClick: function (ev) {
            ev.preventDefault();
            var self = this;
            
            // Get the selected records or all visible records
            var selectedRecords = this.getSelectedRecords();
            if (!selectedRecords.length) {
                this.displayNotification({
                    title: _t("No Records Selected"),
                    message: _t("Please select records to publish."),
                    type: 'warning',
                });
                return;
            }
            
            // Get the IDs of the selected records
            var recordIds = selectedRecords.map(function(record) {
                return record.res_id;
            });
            
            // Show processing message
            this.displayNotification({
                title: _t("Publishing Products"),
                message: _t("Publishing selected products..."),
                type: 'info',
            });
            
            // Use direct SQL approach via a controller to avoid singleton errors
            this._rpc({
                route: '/bom_bulk_product_publish/publish_direct',
                params: {
                    'product_ids': recordIds
                },
            }).then(function(result) {
                if (result.success) {
                    self.displayNotification({
                        title: _t("Success"),
                        message: _t("%s products have been published successfully!", result.count),
                        type: 'success',
                    });
                    self.reload();
                } else {
                    self.displayNotification({
                        title: _t("Error"),
                        message: result.message || _t("An error occurred while publishing products."),
                        type: 'danger',
                    });
                }
            }).guardedCatch(function(error) {
                self.displayNotification({
                    title: _t("Error"),
                    message: _t("An error occurred while publishing products."),
                    type: 'danger',
                });
            });
        }
    });
});