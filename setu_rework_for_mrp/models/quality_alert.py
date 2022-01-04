# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, api, models, _
from odoo import exceptions


class QualityAlert(models.Model):
    _inherit = "quality.alert"

    rework_work_center_id = fields.Many2one("mrp.workcenter", string="Rework Work Center", copy=False)

    def create_new_work_order(self):
        """
        Added By : Ajay Rathod
        Added On : 26-sept-2021
        Use : Create new work order(rework) from quality alert
        :return:
        """
        if not self.rework_work_center_id:
            raise exceptions.ValidationError('Please Select a Rework Work Center')
        rec = self.workorder_id.copy()
        rec.write({'state': 'ready', 'workcenter_id': self.rework_work_center_id.id, 'name': rec.name + ' (Rework)'})
        self.workorder_id.write({'rework_workorder_id': rec.id, 'state': 'rework'})
        mo = self.env['mrp.workorder'].search([('next_work_order_id', '=', rec.id)])
        mo.write({'next_work_order_id': False})
        self.workorder_id.button_pending()
        return rec

    @api.model
    def create(self, vals):
        res = super(QualityAlert, self).create(vals)
        if res.workorder_id and res.workorder_id.state not in ['done', 'cancel', 'rework']:
            res.workorder_id.write({'state': 'rework'})
        return res
