from odoo.tests.common import TransactionCase
from odoo.tools import test_reports
import os
import inspect
from lxml import etree
from io import StringIO
from odoo import fields

class MyTestCase(TransactionCase):
    EXAMPLE_XML = os.path.dirname(__file__) + '/example_soap_header.xml'
    HEADER_XSD = os.path.dirname(__file__) + '/finvoice_soap_header.xsd'

    RI_EXAMPLE_FILE_ADD = os.path.dirname(__file__) + '/' + 'receiver_information_nordea_example_add.xml'

    def setUp(self):
        super(MyTestCase, self).setUp()
        print(inspect.stack()[0][3])


        company = self.env.user.company_id
        partner = self.env['res.partner'].search([('company_id', '=', company.id)])[0]

        # Create invoice out 40
        invoice = self.env['account.invoice'].create({
            'type': 'out_invoice',
            'number': '800014',
            'partner_id': partner.id,
        })

        self.env['account.invoice.line'].create({
            'invoice_id': invoice.id,
            'product_id': self.env['product.product'].search([('company_id', '=', self.env.user.company_id.id)])[0].id,
            'name': 'invoice line name',
            'account_id': self.env['product.product'].search([('company_id', '=', self.env.user.company_id.id)])[
                0].property_account_income_id.id,
            'quantity': 1,
            'price_unit':  40,
        })

        invoice.action_invoice_open()

        # Create invoice in 140
        invoice2 = self.env['account.invoice'].create({
            'type': 'in_invoice',
            'number': '800015',
            'partner_id': partner.id,
        })

        self.env['account.invoice.line'].create({
            'invoice_id': invoice2.id,
            'product_id': self.env['product.product'].search([('company_id', '=', self.env.user.company_id.id)])[0].id,
            'name': 'invoice line name',
            'account_id': self.env['product.product'].search([('company_id', '=', self.env.user.company_id.id)])[
                0].property_account_expense_id.id,
            'quantity': 1,
            'price_unit': 140,
        })

        invoice2.action_invoice_open()


    def test_profit_and_loss_report(self):
        print(inspect.stack()[0][3])

        report_id = self.env['ir.actions.report'].search([('report_name', '=', 'account.report_financial')], limit=1)
        ids = self.env[report_id.model].search([('name', '=', 'Tuloslaskelma (FIN)')])
        ctx = \
            {
                'active_model': report_id.model,
                'active_id': ids[0],
                'date_to': fields.Date.today(),
                'date_from': fields.Date.today(),
            }

        data_dict = \
            {  # 'chart_account_id': ref('account.chart0'),
                'account_report_id': [self.ref('l10n_fi_reports.acc_fin_rep_no_accs_profitandloss_fin'),self.ref('l10n_fi_reports.acc_fin_rep_no_accs_profitandloss_fin')],
                'form':
                    {
                        'account_report_id': [self.ref('l10n_fi_reports.acc_fin_rep_no_accs_profitandloss_fin'),self.ref('l10n_fi_reports.acc_fin_rep_no_accs_profitandloss_fin')],
                        'used_context':ctx,
                        'enable_filter':False,
                        'debit_credit': False,
                        'date_to': fields.Date.today(),
                        'date_from': fields.Date.today(),
                        'date_to_cmp': False,
                        'date_from_cmp': False,
                        'target_move': 'all',
                        'separate_sum_and_header': False,
                        'hide_zero_reports': False
                    }
            }


        res_data, res_format = report_id.with_context(ctx).render_qweb_html(ids, data_dict)
        tmp = res_data.decode('utf-8').replace('\n', '')
        body_xml = tmp[tmp.find('<body'):tmp.find('</body') + len('</body>')]
        root = etree.parse(StringIO(body_xml))
        sales = root.xpath('//span[text()="Myynti"]/../../..//span')[-1].text
        self.assertEqual(sales,'40.00')
        purchases = root.xpath('//span[text()="Ostot tilikauden aikana"]/../../..//span')[-1].text
        self.assertEqual(purchases, '‑140.00')
        profit = root.xpath('//span[text()="Liikevoitto (-tappio)"]/../../..//span')[-1].text
        self.assertEqual(profit,'‑100.00')

    def test_profit_and_loss_report_with_accounts(self):
        print(inspect.stack()[0][3])

        report_id = self.env['ir.actions.report'].search([('report_name', '=', 'account.report_financial')],
                                                         limit=1)
        ids = self.env[report_id.model].search([('name', '=', 'Tuloslaskelma (FIN) - tilikohtainen')])
        ctx = \
            {
                'active_model': report_id.model,
                'active_id': ids[0],
                'date_to': fields.Date.today(),
                'date_from': fields.Date.today(),
            }

        data_dict = \
            {  # 'chart_account_id': ref('account.chart0'),
                'account_report_id': [self.ref('l10n_fi_reports.acc_fin_report_profitandloss_fin'),
                                      self.ref('l10n_fi_reports.acc_fin_report_profitandloss_fin')],
                'form':
                    {
                        'account_report_id': [self.ref('l10n_fi_reports.acc_fin_report_profitandloss_fin'),
                                              self.ref('l10n_fi_reports.acc_fin_report_profitandloss_fin')],
                        'used_context': ctx,
                        'enable_filter': False,
                        'debit_credit': False,
                        'date_to': fields.Date.today(),
                        'date_from': fields.Date.today(),
                        'date_to_cmp': False,
                        'date_from_cmp': False,
                        'target_move': 'all',
                        'separate_sum_and_header': False,
                        'hide_zero_reports': False
                    }
            }

        res_data, res_format = report_id.with_context(ctx).render_qweb_html(ids, data_dict)
        tmp = res_data.decode('utf-8').replace('\n', '')
        body_xml = tmp[tmp.find('<body'):tmp.find('</body') + len('</body>')]
        root = etree.parse(StringIO(body_xml))
        sales = root.xpath('//span[text()="Myynti"]/../../..//span')[-1].text
        self.assertEqual(sales, '40.00')
        purchases = root.xpath('//span[text()="Ostot tilikauden aikana"]/../../..//span')[-1].text
        self.assertEqual(purchases, '‑140.00')
        profit = root.xpath('//span[text()="Liikevoitto (-tappio)"]/../../..//span')[-1].text
        self.assertEqual(profit, '‑100.00')