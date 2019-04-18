# -*- coding: utf-8 -*-


from odoo import api, fields, models


class EuVatReportWizard(models.TransientModel):
    _name = "l10n_fi_reports.eu_vat_report_wizard"
    _description = "EU VAT Report Wizard"

    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    group_by_invoice = fields.Boolean(string='Group by Invoice')


    def _build_contexts(self, data):
        result = {}
        return result

    def _print_report(self, data):
        return self.env.ref('l10n_fi_reports.action_eu_vat_report').report_action(self, data=data, config=False)

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'group_by_invoice'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        return self._print_report(data)

