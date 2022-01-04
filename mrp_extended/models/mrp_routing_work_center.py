from odoo import api, fields, models, _


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    allow_next_work_order = fields.Boolean(string="Allow Execution Of Next Work Order?")
