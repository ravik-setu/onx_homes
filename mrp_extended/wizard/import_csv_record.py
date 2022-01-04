import base64
import csv
import os
from io import StringIO
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ImportCsvRecord(models.TransientModel):
    _name = 'import.csv.record'

    file_data = fields.Binary('CSV File')
    file_name = fields.Char('File Name')
    operation = fields.Selection([('bom', 'Bill of Material'), ('operation', 'Operations'),
                                  ('mrp', 'Manufacturing Order')], string='Operation')
    delimiter = fields.Selection([(';', 'Semicolon'), (',', 'Colon'), ('\t', 'Tab')], string='Delimiter', copy=False)

    def import_mrp_bom_from_csv(self):
        """
                Added By : Smith Ponda
                Added On : 01-dec-2021
                Use : Import the csv file and create logbook and attachment
                :return:
                """

        log_book_obj = self.env['import.csv.record.log']
        log_book_line_obj = self.env['import.csv.record.log.line']
        log_book = log_book_obj.create_log_book()
        self.create_attachment(self.file_data, self.file_name, log_book)
        if not self.csv_validator(self.file_name):
            log_book.update({'state': 'fail'})
            message = "The file must have an extension .csv"
            log_book_line_obj.create_log_book_line(log_book, message)
            raise UserError(_(message))
        file_data = self.read_file(log_book)
        bom_dict = self.prepare_bom_import_data(file_data, log_book)
        self.create_bom_from_file_data(bom_dict, log_book)

    def csv_validator(self, xml_name):
        name, extension = os.path.splitext(xml_name)
        return True if extension == '.csv' else False

    def read_file(self, log_book):
        '''
            Read selected file to import inbound shipment report and return Reader to the caller
        '''
        log_book_line_obj = self.env['import.csv.record.log.line']
        imp_file = StringIO(base64.decodestring(self.file_data).decode())
        try:
            reader = csv.DictReader(imp_file, delimiter=self.delimiter)
        except Exception as e:
            log_book.update({'state': 'fail'})
            message = "Something went wrong at the time of reading file "
            log_book_line_obj.create_log_book_line(log_book, message=message)
            raise UserError(message)
        return reader

    def prepare_bom_import_data(self, file_data, logbook):
        """
                Use : Prepare the bom to create bom
                :return:
        """
        bom_dict = {}
        row_count = 1
        for row in file_data:
            row_count += 1
            prod = self.find_product(row.get('Header Material'), logbook, row_count)
            if prod:
                if row.get('Header Material') not in bom_dict.keys():
                    bom_dict.update({prod.default_code: {'quantity': row.get('Quantity'), 'lines': [],
                                                         'version': row.get('version'), 'error': False}})
                prod_comp = self.find_product(row.get('Component Description'), logbook, row_count)
                if not prod_comp:
                    bom_dict.get(prod.default_code)['error'] = True
                bom_dict.get(prod.default_code).get('lines').append(
                    {'product_id': prod_comp.id if prod_comp else row.get('Component Description'),
                     'quantity': row.get('Component Quantity', 0)})
            else:
                bom_dict.update(
                    {row.get('Header Material'): {'quantity': row.get('Quantity', 0), 'lines': [], 'error': True}})

        return bom_dict

    def find_product(self, default_code, logbook, row_count):
        """
                Use : find if the product is available in odoo
                :return:
        """
        log_book_line_obj = self.env['import.csv.record.log.line']
        product_id = self.env["product.product"].search([('default_code', '=', default_code)], limit=1)
        if not product_id:
            product_id = self.env["product.product"].search([('name', '=ilike', default_code)], limit=1)
            if not product_id:
                logbook.update({'state': 'fail'})
                message = "No product found for {} on {} row".format(default_code, row_count)
                log_book_line_obj.create_log_book_line(log_book=logbook, message=message)
                return False
        return product_id

    def create_bom_from_file_data(self, file_data, log_book):
        log_book_line_obj = self.env['import.csv.record.log.line']
        bom_obj = self.env["mrp.bom"]
        bom_line_obj = self.env["mrp.bom.line"]
        mrp_eco_obj = self.env['mrp.eco']
        eco_type = self.env['mrp.eco.type'].search([])
        for key, value in file_data.items():
            if not value.get('error') and value.get('version'):
                product_id = self.env["product.product"].search([('default_code', '=', key)], limit=1)
                available_bom = bom_obj.search(
                    [('version', '=', value.get('version')), ('product_tmpl_id', '=', product_id.product_tmpl_id.id)])
                if available_bom:
                    msg = "There is already a '{}' bom present in version '{}'".format(key, value.get('version'))
                    log_book_line_obj.create_log_book_line(log_book=log_book, message=msg)
                    continue
                bom_id = bom_obj.create(
                    {'product_tmpl_id': product_id.product_tmpl_id.id,
                     'product_qty': value.get('quantity'),
                     'active': False,
                     'version': value.get('version')
                     })
                for line in value.get('lines'):
                    bom_line_obj.create(
                        {'product_id': line.get('product_id'), 'product_qty': line.get('quantity'),
                         'bom_id': bom_id.id})
                plm_id = mrp_eco_obj.create({
                    'name': bom_id.product_tmpl_id.name,
                    'product_tmpl_id': bom_id.product_tmpl_id.id,
                    'type_id': eco_type[0].id,
                    'new_bom_id': bom_id.id
                })
                message = "Bom record created successfully for {}".format(key)
                log_book_line_obj.create_log_book_line(log_book=log_book, message=message, bom_id=bom_id, plm_id=plm_id)
                _logger.info(message)

    def create_attachment(self, data, filename, log_book):
        """
                Added By : Smith Ponda
                Added On : 01-dec-2021
                Use : create attachment which is attached  in the  BOM record
                :return:
        """

        att = self.env['ir.attachment'].create({
            'name': filename,
            'datas': data,
            'res_model': 'import.csv.record.log',
            'res_id': log_book.id,
            'type': 'binary',
        })

    def import_operation_from_csv(self):
        """
        Added By: Mitrarajsinh Jadeja | Date: 3rd Jan,2021 | Task: 589
        Use: This method will Import Operations from CSV
        """
        log_book_obj = self.env['import.csv.record.log']
        log_book_line_obj = self.env['import.csv.record.log.line']
        log_book = log_book_obj.create_log_book()
        self.create_attachment(self.file_data, self.file_name, log_book)
        log_book.write({'operation': self.operation})
        if not self.csv_validator(self.file_name):
            log_book.update({'state': 'fail'})
            message = "The file must have an extension .csv"
            log_book_line_obj.create_log_book_line(log_book, message)
        file_data = self.read_file(log_book)
        validated_dict_data = self.validate_csv_dict_data(file_data, log_book)
        operation_data = self.prepare_operation_dict_data(validated_dict_data, log_book)
        self.create_and_update_operation_data(operation_data)

    def validate_csv_dict_data(self, file_data, log_book):
        """
        Added By: Mitrarajsinh Jadeja | Date: 3rd Jan,2021 | Task: 589
        Use: This method will validate csv data and prepare dictionary data
        """
        data = []
        log_book_line_obj = self.env['import.csv.record.log.line']
        file_headers = ['Operation', 'Work Center', 'Quality Point', 'Operation Types', 'Bom Products', 'Version']
        required_headers = ['Operation', 'Work Center', 'Bom Products', 'Version']
        row_number = 1
        for row in file_data:
            row_number += 1
            row_temp_data = {'row_number': row_number}
            missing_column_data = []
            missing_required_data = []
            for column in file_headers:
                column_data = row.get(column)
                if not column_data:
                    if column in required_headers:
                        missing_required_data.append(column)
                    missing_column_data.append(column)
                else:
                    row_temp_data.update({column: column_data})
            if missing_column_data:
                message = "{} Data is missing at Row Number: {}".format(", ".join(missing_column_data), row_number)
                log_book_line_obj.create_log_book_line(log_book=log_book, message=message)

            if not missing_required_data:
                data.append(row_temp_data)
        return data

    def prepare_operation_dict_data(self, validated_dict_data, log_book):
        """
        Added By: Mitrarajsinh Jadeja | Date: 3rd Jan,2021 | Task: 589
        Use: This method will prepare dictionary which data needs to import
        """
        operation_dict_data = {}
        mrp_workcenter_obj = self.env['mrp.workcenter']
        log_book_line_obj = self.env['import.csv.record.log.line']
        bom_not_found = []
        for row in validated_dict_data:
            bom_product_name = row.get('Bom Products')

            # Skip if BOM is not found in Odoo
            if bom_product_name in bom_not_found:
                continue

            # Maintain `error` flag to identify data needs to import for BOM or not
            if not operation_dict_data.get(bom_product_name, False):
                operation_dict_data.update({bom_product_name: {'error': False, 'operation': []}})

            row_number = row.get('row_number')
            operation_name = row.get('Operation')
            work_center_name = row.get('Work Center', False)
            bom_product_version = row.get('Version')
            quality_point = row.get('Quality Point', False)
            operation_type = row.get('Operation Types', False)

            work_center = work_center_name and mrp_workcenter_obj.search([('name', '=', work_center_name)])
            if not work_center:
                operation_dict_data.get(bom_product_name).update({'error': True})
                message = "Work Center is not available with [{}] in Odoo. Row " \
                          "Number: {}".format(work_center_name, row_number)
                log_book_line_obj.create_log_book_line(log_book=log_book, message=message)

            if not operation_type or not quality_point:
                operation_dict_data.get(bom_product_name).update({'error': True})

            # Search Bom Product
            product_id = self.env['product.product'].search([('default_code', '=', bom_product_name)])
            bom_id = self.find_bom_from_product(product_id, log_book)
            bom_id = bom_id.filtered(lambda x: x.version == int(bom_product_version))

            if not bom_id:
                bom_not_found.append(bom_product_name)
                message = "Bom is not available with [{}] and Version [{}], " \
                          "Row Number: {}".format(bom_product_name, bom_product_version, row_number)
                log_book_line_obj.create_log_book_line(log_book=log_book, message=message)
                continue

            # Prepare Dictionary
            operation_dict_data.get(bom_product_name).get('operation').append({
                'row_number': row_number, 'operation': operation_name,
                'work_center_id': work_center and work_center.id,
                'quality_point': quality_point,
                'operation_type': operation_type, 'bom_id': bom_id
            })
        return operation_dict_data

    def find_bom_from_product(self, product_id, logbook):
        """
        Added By: Mitrarajsinh Jadeja | Date: 3rd Jan,2021 | Task: 589
        Use: This method will find bom from product
        """
        log_book_line_obj = self.env['import.csv.record.log.line']
        bom_obj = self.env["mrp.bom"]
        bom_id = bom_obj.search([('product_id', '=', product_id.id)], limit=1)
        if not bom_id:
            bom_id = bom_obj.search([('product_tmpl_id', '=', product_id.product_tmpl_id.id)], limit=1)
            if not bom_id:
                logbook.update({'state': 'fail'})
                message = "No Bill of Material found for {}".format(product_id.name)
                log_book_line_obj.create_log_book_line(log_book=logbook, message=message)
        return bom_id

    def create_and_update_operation_data(self, data):
        """
        Added By: Mitrarajsinh Jadeja | Date: 3rd Jan,2021 | Task: 589
        Use: This method will create new operations and update existing
             operations with updated product/operation types.
        """
        operation_obj = self.env['mrp.routing.workcenter']
        quality_point_obj = self.env['quality.point']
        for key in data:
            if not data.get(key).get('error'):
                for data in data.get(key).get('operation'):
                    bom_id = data.get('bom_id')
                    operation_name = data.get('operation')
                    work_center_id = data.get('work_center_id')
                    quality_point_title = data.get('quality_point')
                    operation_type_name = data.get('operation_type')

                    # Search Operation
                    operation = operation_obj.search([('name', '=', operation_name),
                                                      ('workcenter_id', '=', work_center_id), ('bom_id', '=', bom_id.id)])
                    if not operation:
                        operation = operation_obj.create(
                            {'name': operation_name, 'bom_id': bom_id.id, 'workcenter_id': work_center_id})

                    # Search Quality Point
                    quality_point = quality_point_obj.search(
                        [('title', '=', quality_point_title), ('operation_id', '=', operation.id)])
                    if not quality_point:
                        quality_point = quality_point_obj.create({'title': quality_point_title, 'operation_id': operation.id})

                    if operation_type_name:
                        picking_type_id = self.env['stock.picking.type'].search([('name', '=', operation_type_name)])
                        if picking_type_id:
                            quality_point_with_picking_type = quality_point.filtered(
                                lambda x: picking_type_id.id in x.picking_type_ids.ids)
                            if not quality_point_with_picking_type:
                                quality_point.write({'picking_type_ids': [(4, picking_type_id.id)]})

                    product_id = bom_id.product_id or bom_id.product_tmpl_id
                    if product_id:
                        quality_point_with_bom_product = quality_point.filtered(lambda x: product_id.id in x.product_ids.ids)
                        if not quality_point_with_bom_product:
                            quality_point.write({'product_ids': [(4, product_id.id)]})
