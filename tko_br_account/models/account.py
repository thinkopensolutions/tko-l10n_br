# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.invoice_id.type == 'in_invoice':
            self.is_required = False  
        return super(AccountInvoiceLine, self)._onchange_product_id()
        
    is_required = fields.Boolean(string='Is Required', default=True)
