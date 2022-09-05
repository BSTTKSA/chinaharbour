# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    project_name = fields.Char(string='Project Name')
    project_code = fields.Char(string='Internal Code')
    channge_code = fields.Char(compute='_change_code')
    fromdate = fields.Date(string='From Date', default=fields.Date.context_today, copy=False)
    todate = fields.Date(string='To Date', default=fields.Date.context_today, copy=False)
    additional_lines = fields.One2many('additional.move.lines', 'move_id', string='Additional Lines')

    def _change_code(self):
        if self.project_name and self.project_code:
            invcode = self.project_name + '-' + self.project_code + '-' + 'INV'
            self.env['account.journal'].sudo().search([('name', '=', 'Customer Invoices')]).write({
                'code': invcode,
            }
            )

    @api.depends('amount_total', 'amount_untaxed', 'l10n_sa_confirmation_datetime', 'company_id', 'company_id.vat')
    def _compute_qr_code_str(self):
        """ Generate the qr code for Saudi e-invoicing. Specs are available at the following link at page 23
        https://zatca.gov.sa/ar/E-Invoicing/SystemsDevelopers/Documents/20210528_ZATCA_Electronic_Invoice_Security_Features_Implementation_Standards_vShared.pdf
        """

        def get_qr_encoding(tag, field):
            company_name_byte_array = field.encode('UTF-8')
            company_name_tag_encoding = tag.to_bytes(length=1, byteorder='big')
            company_name_length_encoding = len(company_name_byte_array).to_bytes(length=1, byteorder='big')
            return company_name_tag_encoding + company_name_length_encoding + company_name_byte_array

        for record in self:
            qr_code_str = ''
            if record.l10n_sa_confirmation_datetime and record.company_id.vat:
                seller_name_enc = get_qr_encoding(1, record.company_id.display_name)
                company_vat_enc = get_qr_encoding(2, record.company_id.vat)
                time_sa = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'),
                                                            record.l10n_sa_confirmation_datetime)
                timestamp_enc = get_qr_encoding(3, time_sa.isoformat())
                # edited by shaimaa (change amount_total to amount_total_signed)
                # (change amount_untaxed to amount_untaxed_signed)
                invoice_total_enc = get_qr_encoding(4, str(record.amount_total_signed))
                total_vat_enc = get_qr_encoding(5, str(record.currency_id.round(
                    record.amount_total_signed - record.amount_untaxed_signed)))

                str_to_encode = seller_name_enc + company_vat_enc + timestamp_enc + invoice_total_enc + total_vat_enc
                qr_code_str = base64.b64encode(str_to_encode).decode('UTF-8')
            record.l10n_sa_qr_code_str = qr_code_str


class LinesAccountMoveRintation(models.Model):
    _name = 'additional.move.lines'

    move_id = fields.Many2one('account.move')
    name = fields.Char(string='Description')
    amount = fields.Float(string='Amount')
