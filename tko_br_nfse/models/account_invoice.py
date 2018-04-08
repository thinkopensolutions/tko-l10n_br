# -*- encoding: utf-8 -*-
import openerp.addons.decimal_precision as dp
from openerp import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_edoc_item_vals(self, line):
        result = super(AccountInvoice, self)._prepare_edoc_item_vals(line)
        result.update({
            'pis_valor_retencao': abs(line.pis_valor_retencao),
            'cofins_valor_retencao': abs(line.cofins_valor_retencao),
            'issqn_valor_retencao': abs(line.issqn_valor_retencao),
            'irrf_valor_retencao': abs(line.irrf_valor_retencao),
            'inss_valor_retencao': abs(line.inss_valor_retencao),
        })
        return result
