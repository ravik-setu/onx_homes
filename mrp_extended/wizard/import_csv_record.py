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
    delimiter = fields.Selection([(';', 'Semicolon'), (',', 'Colon'), ('\t', 'Tab')], string='Delimiter', copy=False)

    def import_mrp_bom_from_csv(self):
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
        bom_dict = {}
        row_count = 1
        for row in file_data:
            row_count += 1
            prod = self.find_product(row.get('Header Material'), logbook, row_count)
            if prod:
                if row.get('Header Material') not in bom_dict.keys():
                    bom_dict.update({prod.default_code: {'quantity': row.get('Quantity'), 'lines': [], 'version': row.get('version'), 'error': False}})
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
                available_bom = bom_obj.search([('version', '=', value.get('version')), ('product_tmpl_id', '=', product_id.product_tmpl_id.id)])
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
        att = self.env['ir.attachment'].create({
            'name': filename,
            'datas': data,
            'res_model': 'import.csv.record.log',
            'res_id': log_book.id,
            'type': 'binary',
        })
