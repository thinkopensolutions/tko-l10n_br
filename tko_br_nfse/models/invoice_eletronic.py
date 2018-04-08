# -*- encoding: utf-8 -*-
import openerp.addons.decimal_precision as dp
from openerp import fields, models, api

class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_values()
        print "_prepare_eletronic_invoice_values................ ELETRONIC", res
        return res