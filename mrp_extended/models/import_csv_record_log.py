from odoo import fields, models, api
from datetime import date


class ImportCsvRecordLog(models.Model):
    _name = 'import.csv.record.log'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "CSV Import Log"
    _order = 'id desc'

    name = fields.Char(string='Name')
    log_date = fields.Date(string='Log Date', default=date.today())
    user_id = fields.Many2one('res.users', string='Responsible', index=True, default=lambda self: self.env.uid)
    log_type = fields.Selection([('success', 'Success'), ('failure', 'Failure')], string='Log Type')
    message = fields.Text(string='Result')
    line_ids = fields.One2many('import.csv.record.log.line', 'log_id', string='Logs')
    state = fields.Selection([('success', 'Succeed'), ('fail', 'Failure'), ('partial', 'Partially Failed')], string='Status', copy=False, readonly=True,
                             help=" * Succeed: Process Done Successfully .\n"" * Failure: Some issue Generated while importing files.\n")

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code("import.csv.record.log")
        vals.update({'name': seq})
        result = super(ImportCsvRecordLog, self).create(vals)
        return result

    def _log_book_seq(self):
        """
        Features:
            - Generate Next sequence of Log Book.
        """
        return self.env['ir.sequence'].next_by_code('import.csv.record.log.seq')

    def create_log_book(self):
        vals = {'state': 'success'}
        log_book_id = self.create(vals)
        return log_book_id


class ImportCsvRecordLogLine(models.Model):
    _name = 'import.csv.record.log.line'
    _description = "CSV Import Log Line"

    log_type = fields.Selection([('mrp_bom', 'Import Bill Of Material'),
                                 ('mrp', 'Import Manufacturing Order')], string='Log Type')
    message = fields.Text(string='Message')
    log_id = fields.Many2one('import.csv.record.log', string='Log')
    bom_id = fields.Many2one('mrp.bom', string='BOM')
    plm_id = fields.Many2one('mrp.eco', string='PLM')
    state = fields.Selection([('success', 'Succeed'), ('fail', 'Failure')], string='Status', copy=False, default='success')

    def create_log_book_line(self, log_book, message, bom_id=False, plm_id=False):
        """
        Added By : Smith Ponda
        Added On : 01-dec-2021
        Use : add values to create method of logbook line
        :return:
        """
        vals = {
            'message': message,
            'log_id': log_book.id,
            'bom_id':  bom_id.id if bom_id else False,
            'plm_id': plm_id.id if plm_id else False
        }
        log_book_line_obj = self.create(vals)
        return log_book_line_obj