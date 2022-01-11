odoo.define('mrp_extended.KanbanRecord', function (require) {
"use strict";

var KanbanRecord = require('web.KanbanRecord');
var core = require('web.core');

var mrpBarcodeKanbanRecord = KanbanRecord.extend({
    /**
     * @override
     * @private
     */
//    start: function() {
//        var self = this;
//        console.log("barcode");
//        core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
//        this._super();
//    },
//
//    _onBarcodeScanned: function(barcode) {
//        var self = this;
//        console.log(barcode);
//        debugger
//        this._rpc({model: 'mrp.production',
//                    method: 'search_mo_and_redirect_work_orders',
//                    args: [0, barcode.toUpperCase()],
//                }).then(function(action) {
//                    self.do_action(action);
//                });
//    },
//    destroy: function () {
//        core.bus.off('barcode_scanned', this, this._onBarcodeScannedcust);
//        this._super();
//    },
});

return mrpBarcodeKanbanRecord;

});

odoo.define('mrp_extended.KanbanController', function (require) {
"use strict";
var KanbanController = require('web.KanbanController');

var mrpBarcodeKanbanController = KanbanController.extend({
    // --------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Do not add a record but open new barcode views.
     *
     * @private
     * @override
     */
});
return mrpBarcodeKanbanController;

});
