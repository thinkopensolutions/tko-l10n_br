# -*- encoding: utf-8 -*-
import openerp.addons.decimal_precision as dp
from openerp import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_edoc_vals(self, inv):
        res = super(AccountInvoice, self)._prepare_edoc_vals(inv)
        # correct taxes values from withholdings
        # NFSe doesn't have direct taxes but only withholdings
        valor_pis = valor_cofins = valor_csll = valor_irrf = 0.0
        print "initial pis................", res['valor_pis']
        for invoice in self:
            for tax in invoice.withholding_tax_lines:
                if tax.tax_id.domain == 'pis':
                    res.update({'valor_pis': tax.amount})
                if tax.tax_id.domain == 'cofins':
                    res.update({'valor_cofins': tax.amount})
                if tax.tax_id.domain == 'csll':
                    res.update({'valor_csll': tax.amount})
                if tax.tax_id.domain == 'irrf':
                    res.update({'valor_irrf': tax.amount})

        print "final pis................", res['valor_pis']

        return res

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        res = super(AccountInvoice, self)._prepare_eletronic_invoice_values()
        print "_prepare_eletronic_invoice_values................ AccountInvoice", res
        return res

