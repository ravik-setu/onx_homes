from odoo import api, fields, models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _render_qweb_html(self, docids, data=None):
        if self.xml_id == 'mrp_extended.action_cost_struct_mrp_production_individual_orders':
            action = self.env.ref('mrp_account_enterprise.action_cost_struct_mrp_production')
            data['context'] and data['context'].update({'mo_wise_cost_analysis': True})
            self = action
        return super(IrActionsReport, self)._render_qweb_html(docids, data=data)
