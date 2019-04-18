# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO Open Source Management Solution
#
#    ODOO Addon module by Sprintit Ltd
#    Copyright (C) 2016 Sprintit Ltd (<http://sprintit.fi>).
#
#
##############################################################################

from odoo import api, fields, models, _

import time
from collections import namedtuple
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

class EUVatReportLogic(models.AbstractModel):
    _name = "report.l10n_fi_reports.eu_vat_report"
    _description = "EU VAT Summary report (Finnish standart)"
    _auto = False

    def get_report_lines(self,data):

        date_from = data.get('form').get('date_from')
        date_to = data.get('form').get('date_to')
        group_by_invoice = data.get('form').get('group_by_invoice')


        #Create SELECT statement
        sql_select = """ select ai.partner_id, 
                sum(sales_material_EU) as sales_material_EU, 
                sum(sales_service_EU) as sales_service_EU, 
                sum(triangulation_sales) as triangulation_sales """

        # add invoice_id to selection if it is used for grouping
        if group_by_invoice:
            sql_select += " ,result.invoice_id "

        # Create FROM statement
        sql_from = """ from (
            select  invoice_id, aml.date as aml_date, 0 as sales_material_EU, (aml.credit - aml.debit) as sales_service_EU, 0 as triangulation_sales ,  aml.company_id
                    from account_move_line as aml
                    join account_move_line_account_tax_rel as amlatr on amlatr.account_move_line_id = aml.id                                                      
                    left join  account_tax_account_tag as atat on  amlatr.account_tax_id = atat.account_tax_id
                left join account_account_tag as aat on atat.account_account_tag_id = aat.id
                where aat.name like '312%'
            union all
            select  invoice_id, aml.date as aml_date, (aml.credit - aml.debit) as sales_material_EU, 0 as sales_service_EU, 0 as triangulation_sales , aml.company_id
                    from account_move_line as aml
                    join account_move_line_account_tax_rel as amlatr on amlatr.account_move_line_id = aml.id                                                      
                    left join  account_tax_account_tag as atat on  amlatr.account_tax_id = atat.account_tax_id
                left join account_account_tag as aat on atat.account_account_tag_id = aat.id
                where aat.name like '311%'
            union all
            select  invoice_id, aml.date as aml_date, 0 as sales_material_EU, 0 as sales_service_EU, (aml.credit - aml.debit) as triangulation_sales , aml.company_id
                    from account_move_line as aml
                    join account_move_line_account_tax_rel as amlatr on amlatr.account_move_line_id = aml.id                                                      
                    left join  account_tax_account_tag as atat on  amlatr.account_tax_id = atat.account_tax_id
                left join account_account_tag as aat on atat.account_account_tag_id = aat.id
                where aat.name like '333%') as result join account_invoice ai on ai.id = result.invoice_id """

        # Create WHERE statement
        sql_where_clause="where result.company_id = %s " % self.env.user.company_id.id
        if date_from:
            sql_where_clause +=" and aml_date >= '%s'" % (date_from,)
        if date_to:
            sql_where_clause +=" and aml_date <= '%s'" % (date_to,)


        # Create GROUP BY statement
        # add invoice_id to selection if it is used for grouping
        sql_invoice_group_by = " invoice_id, " if group_by_invoice else " "
        sql_group_by = " group by " + sql_invoice_group_by + " partner_id  "

        sql = sql_select + sql_from + sql_where_clause + sql_group_by

        self.env.cr.execute(sql)
        results = self.env.cr.fetchall()

        lines = []
        for line in results:
            partner = self.env['res.partner'].search([('id','=',line[0])])

            vals = {
                'partner': partner.name,
                'sales_material_eu': line[1],
                'sales_service_eu': line[2],
                'triagulation_sales': line[3],
                'invoice': self.env['account.invoice'].search([('id', '=', line[4])]).number if group_by_invoice else " ",
                'country_code':partner.vat[:2] if partner.vat else " ",
                'vat':partner.vat[2:] if partner.vat else " "

            }
            lines.append(vals)

        return lines
    
    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))

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
        formated_dates['current_date'] = datetime.now().strftime(date_format)

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'report_lines': self.get_report_lines(data),
            'formated_dates': formated_dates
        }
        return docargs
