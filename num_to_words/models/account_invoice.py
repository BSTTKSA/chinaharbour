# -*- coding: utf-8 -*-

from num2words import num2words
from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = "account.move"

    text_amount = fields.Char(string="Montant en lettre", required=False, compute="amount_to_words")

    @api.depends('amount_total')
    def amount_to_words(self):
        if self.company_id.text_amount_language_currency:
            if len(self.additional_lines) > 0:
                addition = 0
                for add in self.additional_lines:
                    addition += add.amount
                total = self.amount_total + addition
                self.text_amount = num2words(total, to='currency',
                                             lang=self.company_id.text_amount_language_currency)

            else:
                self.text_amount = num2words(self.amount_total, to='currency',
                                             lang=self.company_id.text_amount_language_currency)
