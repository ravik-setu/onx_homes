from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    is_rework = fields.Boolean(string="Is Rework?")

    def button_start(self):
        self.ensure_one()
        self.raise_warning_if_child_not_processed()
        if not self.is_rework:
            self.raise_warning_if_last_wo_not_processed()
        return super(MrpWorkorder, self).button_start()

    def raise_warning_if_child_not_processed(self):
        child_work_orders = self.production_id.get_child_mo_work_orders()
        for wo in child_work_orders.filtered(lambda work_order:work_order != 'cancel'):
            if wo.state != 'done':
                raise UserError(
                    'Work Order "{}" of Child Manufacturing Order "{}" are not Finished Yet'.format(wo.name,
                                                                                                    wo.production_id.name))
        child_work_orders and self.raise_warning_if_qc_pending(child_work_orders)

    def raise_warning_if_last_wo_not_processed(self):
        last_work_order = self.search([('next_work_order_id', '=', self.id)])
        if last_work_order and not last_work_order.operation_id.allow_next_work_order and self.production_id.name:
            if last_work_order.state not in ('done', 'cancel'):
                raise UserError(
                    "Work order {} - {} is not processed please complete it first!!!".format(self.production_id.name,
                                                                                             last_work_order.name))
        return True

    def button_finish(self):
        self.raise_warning_if_qc_pending()
        return super(MrpWorkorder, self).button_finish()

    def raise_warning_if_qc_pending(self, work_order_ids=False):
        work_order_ids = self if not work_order_ids else work_order_ids
        checks_not_process = work_order_ids.mapped('check_ids').filtered(
            lambda c: c.quality_state == 'none' and c.test_type not in (
                'register_consumed_materials', 'register_byproducts'))
        if checks_not_process:
            error_msg = _(
                'Please go in the Operations tab and perform the following work orders and their quality checks:\n')
            for check in checks_not_process:
                error_msg += check.workorder_id.workcenter_id.name + ' - ' + check.name
                if check.title:
                    error_msg += ' - ' + check.title
                error_msg += '\n'
            raise UserError(error_msg)
        return True

    def do_finish(self):
        res = super(MrpWorkorder, self).do_finish()
        if not self.env.context.get('from_production_order'):
            return self.do_finish_and_list_related_orders()
        return res

    def do_finish_and_list_related_orders(self):
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_workorder_todo")
        child_ids = self.production_id.get_child_mo_work_orders()
        child_ids += self
        production_id = [self.id] if not child_ids else child_ids.mapped('production_id')
        action['domain'] = expression.AND([[('production_id', 'in', production_id.ids)]])
        view = self.env.ref('mrp.workcenter_line_kanban')
        action['views'] = [(view.id, 'kanban')]
        return action
