from odoo import api, fields, models, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    work_order_count = fields.Integer(compute='_compute_work_orders')

    def action_view_mrp_work_orders(self):
        self.ensure_one()
        child_wo_ids = self.get_child_mo_work_orders()
        work_orders = child_wo_ids.ids + self.workorder_ids.ids
        view = self.env.ref('mrp.workcenter_line_kanban')
        action = {
            'name': _('Work Orders'),
            'res_model': 'mrp.workorder',
            'type': 'ir.actions.act_window',
            'views': [(view.id, 'kanban')],
            'view_mode': 'kanban',
            'domain': [('id', 'in', work_orders)],
        }

        return action

    def _compute_work_orders(self):
        for wo in self:
            wo.work_order_count = len(wo.workorder_ids) + len(
                wo.procurement_group_id.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids.workorder_ids)

    def get_child_mo_work_orders(self):
        return self.procurement_group_id.stock_move_ids.created_production_id.workorder_ids
