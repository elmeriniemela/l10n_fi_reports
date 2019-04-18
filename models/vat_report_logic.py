# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models, _, release
from collections import namedtuple
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

VATReportLine= namedtuple("VATReportLine","text tagid type sign")




class ReportVat(models.AbstractModel):
    _name = 'report.l10n_fi_reports.report_vat'

    #Following data structure defines report layout. Each line is defined as combination of description
    #tag for account move line data filtering and type - defining which value need to be summed up for this line
    _vat_report_structure = [
        VATReportLine(text="24 %:n vero", tagid="301-sales24", type="tax", sign=-1),
        VATReportLine(text="14 %:n vero", tagid="302-sales14", type="tax", sign=-1),
        VATReportLine(text="10 %:n vero", tagid="303-sales10", type="tax", sign=-1),
        VATReportLine(text="Vero tavaraostoista muista EU-maista", tagid="305-purchases-material-EU", type="tax", sign=-1),
        VATReportLine(text="Vero palveluostoista muista EU-maista", tagid="306-purchases-service-EU", type="tax", sign=-1),
        VATReportLine(text="Vero tavaroiden maahantuonneista EU:n ulkopuolelta", tagid="340-import-payable", type="tax", sign=-1),
        VATReportLine(text="Vero rakentamispalvelun ja metalliromun ostoista (käännetty verovelvollisuus)", tagid="318-purchases-construct", type="tax", sign=-1),
        VATReportLine(text="Verokauden vähennettävä vero", tagid="307-purchases", type="tax", sign=1),
        VATReportLine(text="Maksettava vero / Palautukseen oikeuttava vero (‒)", tagid="", type="tax-sum", sign=-1),
        VATReportLine(text=" ", tagid="", type="empty-line", sign=-1),
        VATReportLine(text="0-verokannan alainen liikevaihto", tagid="304-sales0", type="net-amount", sign=-1),
        VATReportLine(text="Tavaroiden myynnit muihin EU-maihin", tagid="311-sales-material-EU", type="net-amount", sign=-1),
        VATReportLine(text="Palvelujen myynnit muihin EU-maihin", tagid="312-sales-service-EU", type="net-amount", sign=-1),
        VATReportLine(text="Tavaraostot muista EU-maista", tagid="305-purchases-material-EU", type="net-amount", sign=1),
        VATReportLine(text="Palveluostot muista EU-maista", tagid="306-purchases-service-EU", type="net-amount", sign=1),
        VATReportLine(text="Tavaroiden maahantuonnit EU:n ulkopuolelta", tagid="340-import-payable", type="net-amount", sign=1),
        VATReportLine(text="Rakentamispalvelun ja metalliromun myynnit (käännetty verovelvollisuus)", tagid="319-sales-construct", type="net-amount", sign=-1),
        VATReportLine(text="Rakentamispalvelun ja metalliromun ostot (käännetty verovelvollisuus)", tagid="318-purchases-construct", type="net-amount", sign=1)
    ]

    def get_tax_lines(self, data):
        """Agregate using sql query tax and base ammounts grouped by tagids"""

        where_clause="where aml_tax_and_base.company_id = %s " % self.env.user.company_id.id
        date_from = data.get('form').get('date_from')
        date_to = data.get('form').get('date_to')

        if date_from:
            where_clause +=" and aml_tax_and_base.date >= '%s'" % (date_from,)
        if date_to:
            where_clause +=" and aml_tax_and_base.date <= '%s'" % (date_to,)

        #add companyid

        sql = """select
        coalesce(sum(aml_tax_and_base.deb_tax - aml_tax_and_base.cred_tax),0) as cred_bal_tax,
        coalesce(sum(aml_tax_and_base.deb_base - aml_tax_and_base.cred_base),0) as cred_bal_net,
        aat.name
        from
        (select 0 as deb_tax, 0 as cred_tax, aml_move.debit as deb_base, aml_move.credit as cred_base, aml_move.name, amlatr.account_tax_id, date, company_id
        from account_move_line as aml_move
        join account_move_line_account_tax_rel as amlatr on amlatr.account_move_line_id = aml_move.id
        union all
        select aml_tax.debit as deb_tax, aml_tax.credit as cred_tax, 0 as deb_base, 0 as cred_base, aml_tax.name, aml_tax.tax_line_id as account_tax_id, date, company_id
        from account_move_line as aml_tax where aml_tax.tax_line_id is not null
        ) as aml_tax_and_base
        join account_tax_account_tag as atat on aml_tax_and_base.account_tax_id = atat.account_tax_id
        join account_account_tag as aat on atat.account_account_tag_id = aat.id """+where_clause+""" group by aat.id"""

        if data.get('form').get('cash_based'):
            for field in ['debit', 'credit', 'balance']:
                sql = sql.replace(field, field + '_cash_basis')

        lines=dict()

        self.env.cr.execute(sql)
        results = self.env.cr.fetchall()
        for tax in results:
            vals = {
                'tax': tax[0],
                'net-amount': tax[1]
            }
            lines[tax[2]]=vals #tax code name : balance

        lines['scope-purchases']={'scope-purchases': self.get_scope_purchase(data)}

        return lines

    def get_tax_accounts(self, data):
        tag_accounts = dict()
        for report_line in self._vat_report_structure: #iterate ove tag id's
            if report_line.type in ["tax","net-amount"]:
                tag_data= []
                tax_codes=self.env["account.tax"].search([('tag_ids','=',report_line.tagid)])
                for tax_code in tax_codes: #iterate over tax-codes
                    tax_accounts=[]
                    base_accounts=[]
                    tax_balances_and_accounts = self.get_accounts_by_tax(tax_code.id, data)
                    base_balances_and_accounts = self.get_base_amount_by_tax(tax_code.id, data)

                    for acc in tax_balances_and_accounts: #iterate over tax accounts
                        vals_acc_tax = {
                            'balance': acc[0],
                            'code': acc[1],
                            'name': acc[2]
                         }
                        tax_accounts.append(vals_acc_tax)
                    for acc in base_balances_and_accounts: #iterate over base accounts
                        vals_acc_base={
                            'balance': acc[0],
                            'code': acc[1],
                            'name': acc[2]
                         }
                        base_accounts.append(vals_acc_base)
                    vals_tax = {
                        'tax': tax_accounts,
                        'net-amount': base_accounts,
                        'tax-code': tax_code.name
                    }
                    tag_data.append(vals_tax)
                tag_accounts[report_line.tagid]=tag_data

        tag_accounts['scope-purchases'] =  self.get_purchase_scope_accounts(data)

        return tag_accounts

    def get_accounts_by_tax(self, tax_id, data):
        where_clause = "where aml.tax_line_id = %s and aml.company_id = %s " % (tax_id, self.env.user.company_id.id)
        date_from = data.get('form').get('date_from')
        date_to = data.get('form').get('date_to')

        if date_from:
            where_clause +=" and aml.date >= '%s'" % (date_from,)
        if date_to:
            where_clause +=" and aml.date <= '%s'" % (date_to,)

        sql = """select balance, code, name from
                (select coalesce(sum(aml.debit - aml.credit),0) balance, aml.account_id from
                account_move_line aml """ + where_clause + """ group by aml.account_id
                ) as ab join account_account aa on ab.account_id = aa.id"""

        if data.get('form').get('cash_based'):
            for field in ['debit', 'credit', 'balance']:
                sql = sql.replace(field, field + '_cash_basis')

        self.env.cr.execute(sql)
        return self.env.cr.fetchall()

    def get_purchase_scope_accounts(self,  data):

        where_clause = "where aml.company_id = %s " % (self.env.user.company_id.id)
        date_from = data.get('form').get('date_from')
        date_to = data.get('form').get('date_to')

        if date_from:
            where_clause +=" and aml.date >= '%s'" % (date_from,)
        if date_to:
            where_clause +=" and aml.date <= '%s'" % (date_to,)



        sql = """select at.name, aa.name, aa.code,   coalesce(sum(aml.debit - aml.credit),0) balance from account_move_line aml
                join account_tax at on aml.tax_line_id = at.id and type_tax_use = 'purchase' join
                account_account aa on aml.account_id = aa.id """ + where_clause +\
              """ group by aa.name, aa.code, at.name"""


        if data.get('form').get('cash_based'):
            for field in ['debit', 'credit', 'balance']:
                sql = sql.replace(field, field + '_cash_basis')

        self.env.cr.execute(sql)
        accounts_table =  self.env.cr.fetchall()
        tax_codes_and_accounts = dict()
        for acc in accounts_table:  # iterate over tax accounts
            account_data = {
                'balance': acc[3],
                'code': acc[2],
                'name': acc[1]}
            if acc[0] not in tax_codes_and_accounts:
                tax_codes_and_accounts[acc[0]]=[account_data]
            else:
                tax_codes_and_accounts[acc[0]].append(account_data)
        result= []
        if tax_codes_and_accounts:
            for tax_code, account_d in tax_codes_and_accounts.iteritems():
                temp={'tax-code':tax_code, 'scope-purchases':account_d}
                result.append(temp)
        return result

    def get_base_amount_by_tax(self, tax_id, data):
        where_clause = "where amlatr.account_tax_id = %s and aml.company_id = %s " % (tax_id, self.env.user.company_id.id)
        date_from = data.get('form').get('date_from')
        date_to = data.get('form').get('date_to')

        if date_from:
            where_clause +=" and aml.date >= '%s'" % (date_from,)
        if date_to:
            where_clause +=" and aml.date <= '%s'" % (date_to,)

        sql = """select balance, code, name from
                (select coalesce(sum(aml.debit - aml.credit),0) balance, aml.account_id from
                account_move_line aml
                join account_move_line_account_tax_rel as amlatr on amlatr.account_move_line_id = aml.id """ + \
                where_clause + """ group by aml.account_id
                ) as ab join account_account aa on ab.account_id = aa.id"""

        if data.get('form').get('cash_based'):
            for field in ['debit', 'credit', 'balance']:
                sql = sql.replace(field, field + '_cash_basis')

        self.env.cr.execute(sql)
        return self.env.cr.fetchall()

    def get_tax_sum(self, tax_lines):
        net_tax_sum=0
        for report_line in self._vat_report_structure:
            if report_line.type == 'tax' and report_line.tagid in tax_lines:
                net_tax_sum += tax_lines[report_line.tagid]['tax']
        return net_tax_sum

    def get_scope_purchase(self, data):

        where_clause = "where  aml.company_id = %s " % self.env.user.company_id.id
        date_from = data.get('form').get('date_from')
        date_to = data.get('form').get('date_to')

        if date_from:
            where_clause +=" and aml.date >= '%s'" % (date_from,)
        if date_to:
            where_clause +=" and aml.date <= '%s'" % (date_to,)

        sql="""select coalesce(sum(aml.debit - aml.credit),0),  type_tax_use from account_move_line as aml
                join account_tax at on aml.tax_line_id = at.id and type_tax_use = 'purchase' """ + where_clause + \
                """ group by type_tax_use"""

        if data.get('form').get('cash_based'):
            for field in ['debit', 'credit', 'balance']:
                sql = sql.replace(field, field + '_cash_basis')

        self.env.cr.execute(sql)
        results = self.env.cr.fetchall()
        if len(results) > 0:
            return results[0][0]
        else:
            return 0
    
    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        #report_lines = self.get_account_lines(data.get('form'))
        tag_ids=data.get('form').get('tags')
        tax_lines = self.get_tax_lines(data)
        tax_scope_purchase = self.get_scope_purchase(data)
        tax_lines_accounts=[]
        purchase_scope_accounts=[]
        if data.get('form').get('detailed_report'):
            tax_lines_accounts = self.get_tax_accounts(data)

        #formatting dates
        date_fields=['date_to','date_from']
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

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_tax_lines': tax_lines, #
            'report_lines': self._vat_report_structure, #
            'get_tax_sum': self.get_tax_sum(tax_lines), #
            'get_tax_lines_accounts': tax_lines_accounts, #
            'formated_dates': formated_dates

        }
        return docargs

