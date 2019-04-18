# -*- coding: utf-8 -*-

from openerp import api, fields, models


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

        return self.env['report'].get_action(self, 'l10n_fi_reports.report_vat', data=data)

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['tags','date_from','date_to','detailed_report','cash_based'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        return self._print_report(data)

