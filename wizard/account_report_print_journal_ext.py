# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountPrintJournal(models.TransientModel):
    _inherit = "account.print.journal"

    journal_ids = fields.Many2many('account.journal', string='Journals', required=True, default=lambda self: self.env['account.journal'].search([]))

