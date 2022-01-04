odoo.define('mrp_extended.barcode_main_menu', function (require) {
'use strict';

var BarcodeMainMenu = require('stock_barcode.MainMenu').MainMenu;
BarcodeMainMenu.include({
   events: _.defaults({
        'click .button_manufacturing':  function(){
            this.do_action('mrp_extended.mrp_kanban_production_action');
        }
    }, BarcodeMainMenu.prototype.events),

    });
});