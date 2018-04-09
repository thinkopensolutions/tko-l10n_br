# -*- encoding: utf-8 -*-
import openerp.addons.decimal_precision as dp
from openerp import fields, models, api

STATE = {'edit': [('readonly', False)]}
class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    valor_retencao_inss = fields.Monetary(
        string=u"Retenção INSS", readonly=True, states=STATE)

    # FIX withholdings on NFSe emission
    @api.multi
    def _prepare_eletronic_invoice_values(self):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_values()
        if res.get('lista_rps'):
            res['lista_rps'][0].update({
                'valor_pis': str("%.2f" % self.valor_retencao_pis),
                'valor_cofins': str("%.2f" % self.valor_retencao_cofins),
                'valor_csll': str("%.2f" % self.valor_retencao_csll),
                'valor_inss': str("%.2f" % self.valor_retencao_inss),
                'valor_ir': str("%.2f" % self.valor_retencao_irrf),
            })
        return res
