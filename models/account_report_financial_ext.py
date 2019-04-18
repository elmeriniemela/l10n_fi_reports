# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models, _
# from . import account_financial_report_ext
from odoo.addons.l10n_fi_reports.models.account_financial_report_ext import account_financial_report_ext
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.config import config

class ReportFinancial(models.AbstractModel):
    _inherit = 'report.account.report_financial'
    ACCOUNT_LINE_DEF_LEVEL=6

    def get_account_lines(self, data):

        # Class account_financial_report should nbe informed wether sums and header need to be printed separately
        account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
        account_report.setSeparateSumAndHeader(data['separate_sum_and_header'])

        # If zero transactions lines and hierarchies need to be removed debit credit info is needed
        temp_data = dict(data)
        temp_data['debit_credit'] = True
        bal_lines = super(ReportFinancial, self).get_account_lines(temp_data)

        # If we want to find zero transaction reports and hierarchies from comparable period we need debit credit information for it
        bal_lines_cmp = None
        if data['enable_filter']:
            temp_data['date_from'] = data['date_from_cmp']
            temp_data['date_to'] = data['date_to_cmp']
            temp_data['date_from_cmp'] = data['date_from']
            temp_data['date_to_cmp'] = data['date_to']
            temp_data['used_context']['date_from'] = data['date_from_cmp']
            temp_data['used_context']['date_to'] = data['date_to_cmp']
            temp_data['used_context']['date_from_cmp'] = data['date_from']
            temp_data['used_context']['date_to_cmp'] = data['date_to']
            temp_data['comparison_context']['date_to'] = data['date_to']
            temp_data['comparison_context']['date_from'] = data['date_from']
            bal_lines_cmp = super(ReportFinancial, self).get_account_lines(temp_data)

        # Removing zero transactions lines and hierrchies. On each level identify lines with no cred, deb events
        # If a line preceeding the line to be deleted is a header, delete it as well
        if (data['hide_zero_reports']):
            maxlevel = max(rep_line['level'] for rep_line in bal_lines)
            for lev in range(maxlevel, 0, -1):
                to_be_deleted_sums_idxs = [i for i, x in enumerate(bal_lines) if x['level'] == lev and
                                           x['credit'] == 0 and x['debit'] == 0 and x['account_type'] in ['sum',
                                                                                                          'account_type']]
                # If comparable period active find zero transaction lines and hierarchies for cmp period
                if data['enable_filter']:
                    to_be_deleted_sums_cmp_idxs = [i for i, x in enumerate(bal_lines_cmp) if x['level'] == lev and
                                                   x['credit'] == 0 and x['debit'] == 0 and
                                                   x['account_type'] in ['sum', 'account_type']]
                    to_be_deleted_sums_idxs = set(to_be_deleted_sums_idxs) & set(to_be_deleted_sums_cmp_idxs)

                to_be_deleted_headers_idxs = set([x - 1 for x in to_be_deleted_sums_idxs if
                                                  bal_lines[x - 1]['account_type'] == 'header' and
                                                  bal_lines[x]['name'] == bal_lines[x - 1]['name']])

                to_be_deleted_union = set(to_be_deleted_sums_idxs) | set(to_be_deleted_headers_idxs)

                for index in sorted(to_be_deleted_union, reverse=True):
                    del bal_lines[index]
                    if data['enable_filter']:
                        del bal_lines_cmp[index]  # remove records from cmp set as well, otherwise indexes won't match

        # Set individual account lines to have biggest level for proper intending in report
        for line in bal_lines:
            if line['type'] == 'account':
                line['level'] = self.ACCOUNT_LINE_DEF_LEVEL

        # If headers and sums were separated move account lines to follow account types
        if data['separate_sum_and_header']:
            idx_account_sum_to_be_moved = None
            for idx, line in enumerate(bal_lines):
                if idx_account_sum_to_be_moved is not None and line['type'] != 'account':
                    line__account_sum_to_be_moved = bal_lines.pop(idx_account_sum_to_be_moved)
                    bal_lines.insert(idx - 1, line__account_sum_to_be_moved)
                    idx_account_sum_to_be_moved = None
                if line['account_type'] == 'account_type':
                    idx_account_sum_to_be_moved = idx

        # Calculate cumulative sum
        cum_sum_balance = 0
        cum_sum_credit = 0
        cum_sum_debit = 0
        cum_sum_bal_cmp = 0
        for line in bal_lines:
            if line['account_type'] == 'cumulative':
                line['balance'] = cum_sum_balance
                line['credit'] = cum_sum_credit
                line['debit'] = cum_sum_debit
                line['balance_cmp'] = cum_sum_bal_cmp
            if line['account_type'] in ['accounts', 'account_type']:
                cum_sum_balance += line['balance']
                cum_sum_credit += line['credit']
                cum_sum_debit += line['debit']
                if data['enable_filter']:
                    cum_sum_bal_cmp += line['balance_cmp']

        return bal_lines

    def split_bal_lines_into_pages(self, bal_lines):
        pages = [[]]
        for line in bal_lines:
            if (line['name']== account_financial_report_ext.PAGE_BREAK_REPORT_NAME):
               pages.append([])
            else:
                pages[-1].append(line)
        return pages
    
    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        report_lines = self.get_account_lines(data.get('form'))
        
        pages = self.split_bal_lines_into_pages(report_lines)
        if data['form']['enable_filter']:
            data['form']['debit_credit']=False

        #formatting dates
        date_fields=['date_to','date_from','date_from_cmp', 'date_to_cmp']
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        #depending on whether environmen v9 or v10 is used date formatting is obtainen differently
        date_format = lang_id.date_format
        formated_dates=dict()
        for field in date_fields:
            if data['form'][field]:
                formated_dates[field] = datetime.strptime(data['form'][field], DEFAULT_SERVER_DATE_FORMAT).strftime(date_format)
            else:
                formated_dates[field] = ""
        formated_dates['current_date'] =datetime.now().strftime(date_format)
        
        
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_account_lines': report_lines,
            'pages':pages,
            'page_count':len(pages),
            'formated_dates': formated_dates
        }