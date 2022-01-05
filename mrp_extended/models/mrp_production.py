from odoo import api, fields, models, _
import base64


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    work_order_count = fields.Integer(compute='_compute_work_orders')
    work_order_done = fields.Integer("Done Work Orders", compute="_compute_work_orders")

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
            work_orders = wo.workorder_ids + wo.procurement_group_id.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids.workorder_ids

            wo.work_order_count = len(work_orders)
            wo.work_order_done = len(work_orders.filtered(lambda x: x.state == "done"))

    def get_child_mo_work_orders(self):
        workorder_ids = self.procurement_group_id.stock_move_ids.created_production_id.workorder_ids
        for wo in workorder_ids:
            workorders = wo.production_id.procurement_group_id.stock_move_ids.created_production_id.workorder_ids
            for order in workorders:
                if order not in workorder_ids:
                    workorder_ids += order
        return workorder_ids

    def get_parent_mos(self):
        parent_mos = self.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.mrp_production_ids - self
        for rec in parent_mos:
            parent_mo = rec.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.mrp_production_ids - rec
            if parent_mo and parent_mo not in parent_mos:
                parent_mos += parent_mo
        return parent_mos

