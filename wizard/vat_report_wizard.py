# -*- coding: utf-8 -*-

from odoo import api, fields, models


class VatReport(models.TransientModel):
    _name = "l10n_fi_reports.vat.report"
    _description = "VAT Period Report"

    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')

    tags = fields.Many2many('account.account.tag', string='Tags', required=True, default=lambda self: self.env['account.account.tag'].search([['applicability','=','taxes']]))
    detailed_report = fields.Boolean(string='Details')
    cash_based = fields.Boolean(string='Cash Based')


    def _build_contexts(self, data):
        result = {}
        return result

    
    def _print_report(self, data):
        return self.env.ref('l10n_fi_reports.action_report_vat').report_action(self, data=data, config=False)

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        #data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        #data['form'] = self.read(['date_from', 'date_to', 'journal_ids'])[0]
        data['form'] = self.read(['tags','date_from','date_to','detailed_report','cash_based'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        return self._print_report(data)

