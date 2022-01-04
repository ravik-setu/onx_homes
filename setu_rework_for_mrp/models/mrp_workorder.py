# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.osv import expression
from odoo.exceptions import UserError


class MrpWorkcenterLine(models.Model):
    _inherit = "mrp.workorder"

    state = fields.Selection(selection_add=[('rework', 'Rework')])
    rework_workorder_id = fields.Many2one("mrp.workorder", copy=False)

    def do_fail(self):
        """
        Added By : Ajay Rathod
        Added On : 26-sept-2021
        Use : To create quality alert while QC get Fail
        :return:
        """
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("quality_control.quality_alert_action_check")
        action['target'] = 'new'
        action['views'] = [(False, 'form')]
        action['context'] = {
            'display_show': False,
            'default_company_id': self.company_id.id,
            'default_product_id': self.product_id.id,
            'default_product_tmpl_id': self.product_id.product_tmpl_id.id,
            'default_workorder_id': self.id,
            'default_production_id': self.production_id.id,
            'default_workcenter_id': self.workcenter_id.id,
            'discard_on_footer_button': True,
            'default_title': self.name + ' - ' + self.production_id.name
        }
        return action

    def do_finish(self):
        """
        Added By : Ravi Kotadiya
        Added On : 26-sept-2021
        Use : Mark parent MO as done while work order mark as done
        :return:
        """
        self.find_parent_wo_and_mark_done()
        return super(MrpWorkcenterLine, self).do_finish()

    def find_parent_wo_and_mark_done(self):
        """
        Added By : Ravi Kotadiya
        Added On : 28-sept-2021
        Use : To find the parent work order of Re-work and mark as finish while user mark rework order as finish
        :return:
        """
        parent_wos = self.search([('rework_workorder_id', '=', self.id)])
        for wo in parent_wos:
            for qc in wo.check_ids.filtered(lambda check: check.quality_state == 'none'):
                qc.do_pass()
            wo.do_finish()

    def button_start(self):
        """
        Added By : Ravi Kotadiya
        Added On : 28-sept-2021
        Use : avoid to start the work order if work order contains the re-work work order
        :return:
        """
        if self.state == 'rework' and self.rework_workorder_id:
            return True
        return super(MrpWorkcenterLine, self).button_start()

    def action_cancel(self):
        res = super(MrpWorkcenterLine, self).action_cancel()
        if self.rework_workorder_id:
            self.rework_workorder_id.action_cancel()
        return res
