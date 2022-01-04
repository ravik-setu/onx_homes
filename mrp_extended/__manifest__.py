# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'MRP Extended',
    'version': '14.0',
    'category': 'sale',
    'summary': """ """,
    'website': 'https://www.setuconsulting.com',
    'support': 'support@setuconsulting.com',
    'description': """
     
    """,
    'author': 'Setu Consulting Services Pvt. Ltd.',
    'license': 'OPL-1',
    'sequence': 25,
    'depends': ['stock_barcode', 'sale_stock', 'mrp_account_enterprise'],
    'images': ['static/description/banner.gif'],
    'data': [
        'data/ir_sequence_view.xml',
        'security/ir.model.access.csv',
        'views/js_controller_view.xml',
        'views/mrp_production_view.xml',
        'views/mrp_routing_work_center_view.xml',
        'views/mrp_account_view.xml',
        'views/import_csv_record_log_view.xml',
        'wizard/import_csv_record_view.xml'
    ],
    'qweb': [
        'views/barcode_view.xml'
    ],
    'application': True,
    # 'pre_init_hook': 'pre_init',
    'live_test_url': 'http://95.111.225.133:5929/web/login',
}
