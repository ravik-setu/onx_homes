odoo.define('mrp_extended.ListKanbanView', function (require) {
"use strict";

var mrpBarcodeKanbanController = require('mrp_extended.KanbanController');
var mrpBarcodeKanbanRenderer = require('mrp_extended.KanbanRenderer');

var KanbanView = require('web.KanbanView');
var view_registry = require('web.view_registry');

var mrpBarcodeListKanbanView = KanbanView.extend({
	config: _.extend({}, KanbanView.prototype.config, {
		Controller: mrpBarcodeKanbanController,
		Renderer: mrpBarcodeKanbanRenderer,
	}),


});

view_registry.add('mrp_barcode_list_kanban', mrpBarcodeListKanbanView);
return mrpBarcodeListKanbanView;
});
