##############################################################################
#
#    ODOO Open Source Management Solution
#
#    ODOO Addon module by Sprintit Ltd
#    Copyright (C) 2015 Sprintit Ltd (<http://sprintit.fi>).
#
##############################################################################

from odoo import api, fields, models, _



# additional formatting options for report model
class account_financial_report_ext(models.Model):
    _inherit = "account.financial.report"

    PAGE_BREAK_REPORT_NAME = "#REQUIRES_PRECEEDING_PAGEBREAK"

    requires_page_break = fields.Boolean('Requires preceeding page break', oldname='requiresPageBreak', default=False)
    separate_sum_and_header = False

    type = fields.Selection([
        ('sum', 'View'),
        ('header', 'Header'),
        ('accounts', 'Accounts'),
        ('account_type', 'Account Type'),
        ('account_report', 'Report Value'),
        ('cumulative','Cumulative Sum'),
        ], 'Type', default='sum')

    root_element = fields.Many2one("account.financial.report", string="Root element", oldname='rootElement', compute='_compute_root_element', readonly=True, store=True)

    @api.depends('parent_id')
    def _compute_root_element(self):
        for repElement in self:
            repElement.root_element = repElement._find_root()

    def _find_root(self):
        if not self.parent_id.id:
            return self
        else:
            return self.parent_id._find_root()

    def setSeparateSumAndHeader(self, setSeparate):
        account_financial_report_ext.separate_sum_and_header=setSeparate

   