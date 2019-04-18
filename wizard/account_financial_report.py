from odoo import api, fields, models


class AccountingReport(models.TransientModel):
    _inherit = "accounting.report"

    hide_zero_reports = fields.Boolean(string='Hide zero transactions reports', default=True)
    separate_sum_and_header = fields.Boolean(string='Sum below', default=False)
    filter_cmp = fields.Selection([('filter_no', 'No Filters'), ('filter_date', 'Date')], string='Filter by',
                                  required=True, default='filter_date')
    

    @api.multi
    def check_report(self):
        res = super(AccountingReport, self).check_report()
        res['data']['form']['hide_zero_reports']=self.hide_zero_reports
        res['data']['form']['separate_sum_and_header'] = self.separate_sum_and_header
        return res

    def _print_report(self, data):
        data['form'].update(self.read(['date_from_cmp', 'debit_credit', 'date_to_cmp', 'filter_cmp', 'account_report_id',
                                       'hide_zero_reports','enable_filter', 'label_filter','separate_sum_and_header',
                                       'target_move'])[0])
        return self.env.ref('account.action_report_financial').report_action(self, data=data, config=False)