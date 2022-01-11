odoo.define('mrp_extended.KanbanRenderer', function (require) {
"use strict";

var mrpBarcodeKanbanRecord = require('mrp_extended.KanbanRecord');
var core = require('web.core');

var KanbanRenderer = require('web.KanbanRenderer');

var mrpBarcodeListKanbanRenderer = KanbanRenderer.extend({
    config: _.extend({}, KanbanRenderer.prototype.config, {
        KanbanRecord: mrpBarcodeKanbanRecord,
    }),
     start: function() {
        var self = this;
        core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
        this._super();
    },
    _renderView: function () {
            this._super();
            console.log($('.o_content'))
            $('.o_content').focus();
    },
    _onBarcodeScanned: function(barcode) {
        debugger
        var self = this;
        console.log(barcode);
        this._rpc({model: 'mrp.production',
                    method: 'search_mo_and_redirect_work_orders',
                    args: [0, barcode.toUpperCase()],
                }).then(function(action) {
                    self.do_action(action);
                });
    },
    destroy: function () {
        core.bus.off('barcode_scanned', this, this._onBarcodeScannedcust);
        this._super();
    },
});

return mrpBarcodeListKanbanRenderer;

});
