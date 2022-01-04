# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Rework Management for MRP',
    'version': '1.1',
    'category': 'Manufacturing/Quality',
    'sequence': 50,
    'summary': 'Rework Management with MRP',
    'depends': ['quality_mrp_workorder', 'quality_control', 'mrp_workorder', 'barcodes'],
    'description': """
    Adds Quality Control to workorders.
""",
    "data": [
        'views/quality_views.xml',
    ],
    'auto_install': True,
    'license': 'OEEL-1',
}
