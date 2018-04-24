# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountTAX(models.Model):
    _inherit = 'account.tax'

    @api.onchange('domain')
    def _onchange_domain_tax(self):
        if self.domain in ('icms', 'simples', 'pis', 'cofins', 'issqn', 'ii',
                           'icms_inter', 'icms_intra', 'fcp', 'irpj', 'csll',
                           'icmsst', 'ipi'):
            self.price_include = False
            self.tax_discount = True
            self.amount_type = 'percent'



class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.invoice_id.type == 'in_invoice':
            self.is_required = False
        return super(AccountInvoiceLine, self)._onchange_product_id()

    is_required = fields.Boolean(string='Is Required', default=True)
