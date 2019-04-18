# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO Open Source Management Solution
#
#    ODOO Addon module by Sprintit Ltd
#    Copyright (C) 2015 Sprintit Ltd (<http://sprintit.fi>).
#
##############################################################################


{
    'name': 'Finnish accounting reports',
    'version': '0.4',
    'license': 'Other proprietary',
    'category': 'Accounting',
    'description': """
Finnish Legal Statements
========================
This module contains set of reports and pivot tables designed specialy for accounting needs in Finland.

PDF Reports: Balance, Profit and Loss, VAT Period Report, EU VAT Summary report

Other: Journals "Customer Invoices" and "Vendor Bills" limitation removed
    """,
    'author': 'Sprintit ltd',
    'maintainer': 'Sprintit ltd',
    'website': 'http://www.sprintit.fi',
    'depends': [
        'l10n_fi'
    ],
    'data': [
        #'data/financial_reports.xml',
        #'data/financial_reports_with_accounts.xml',
        #'view/report_financial.xml',
        #'wizard/account_financial_report_view_ext.xml',
        'view/report_vat.xml',
        #'view/financial_report_view_ext.xml',
        'wizard/eu_vat_report_view_and_menu.xml',
        'wizard/accout_journal_report.xml',
        'wizard/vat_report_view_and_menu.xml',
        'view/report_eu_vat_summary.xml',
        'view/report_import.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    "external_dependencies": { # python pip packages
    #     'python': ['suds', 'dateutil'],
    },
    'installable': True,
    'auto_install': False,
 }

