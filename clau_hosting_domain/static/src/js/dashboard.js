odoo.define('clau_hosting_domain.dashboard', function (require) {
    "use strict";

    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;

    var ServiceDashboard = AbstractAction.extend({
        template: 'ServiceDashboard',
        events: {
            'click .o_service_dashboard_action': '_onDashboardActionClicked',
        },

        init: function(parent, context) {
            this._super(parent, context);
            this.dashboardData = {};
            this.expiringDomains = [];
            this.expiringHosting = [];
        },

        willStart: function() {
            var self = this;
            return $.when(
                this._super.apply(this, arguments),
                this._fetchData()
            );
        },

        _fetchData: function() {
            var self = this;
            return $.when(
                rpc.query({
                    model: 'domain.service',
                    method: 'search_count',
                    args: [[['status', '=', 'active']]],
                }),
                rpc.query({
                    model: 'domain.service',
                    method: 'search_read',
                    args: [[
                        ['days_to_expire', '<=', 30],
                        ['days_to_expire', '>', 0],
                        ['status', '=', 'active']
                    ]],
                    fields: ['name', 'end_date', 'days_to_expire', 'customer_id', 'domain_provider'],
                    limit: 10
                }),
                rpc.query({
                    model: 'hosting.service',
                    method: 'search_count',
                    args: [[['status', '=', 'active']]],
                }),
                rpc.query({
                    model: 'hosting.service',
                    method: 'search_read',
                    args: [[
                        ['days_to_expire', '<=', 30],
                        ['days_to_expire', '>', 0],
                        ['status', '=', 'active']
                    ]],
                    fields: ['name', 'end_date', 'days_to_expire', 'customer_id', 'hosting_provider'],
                    limit: 10
                }),
                rpc.query({
                    model: 'res.partner',
                    method: 'search_count',
                    args: [[['id', 'in', 
                        rpc.query({
                            model: 'domain.service',
                            method: 'search_read',
                            args: [[['status', '=', 'active']]],
                            fields: ['customer_id'],
                        }).then(function(result) {
                            return result.map(function(r) { return r.customer_id[0]; });
                        })
                    ]]],
                })
            ).then(function(domainCount, expiringDomains, hostingCount, expiringHosting, customerCount) {
                self.dashboardData = {
                    domainCount: domainCount,
                    hostingCount: hostingCount,
                    customerCount: customerCount || 0,
                    totalServices: domainCount + hostingCount
                };
                self.expiringDomains = expiringDomains;
                self.expiringHosting = expiringHosting;
            });
        },
        
        start: function() {
            var self = this;
            return this._super.apply(this, arguments).then(function() {
                self._renderDashboard();
            });
        },
        
        _renderDashboard: function() {
            var $content = $(QWeb.render('ServiceDashboardMain', {
                widget: this,
                data: this.dashboardData,
                expiringDomains: this.expiringDomains,
                expiringHosting: this.expiringHosting
            }));
            this.$el.empty();
            this.$el.append($content);
        },
        
        _onDashboardActionClicked: function(ev) {
            ev.preventDefault();
            var $action = $(ev.currentTarget);
            var actionName = $action.attr('name');
            var actionContext = $action.attr('context');
            this.do_action(actionName, {
                additional_context: actionContext
            });
        },
        
        reload: function() {
            return this._fetchData().then(this._renderDashboard.bind(this));
        },
    });

    core.action_registry.add('service_dashboard', ServiceDashboard);
    
    return ServiceDashboard;
});