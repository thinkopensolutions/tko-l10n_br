# -*- encoding: utf-8 -*-
import openerp.addons.decimal_precision as dp
from openerp import fields, models, api

STATE = {'edit': [('readonly', False)]}


class BrAccountServiceType(models.Model):
    _inherit = 'br_account.service.type'

    issqn_percent = fields.Float(u'Aliquota serviço')

class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    nfse_url = fields.Char('URL', compute='view_nfse', store=False)
    valor_retencao_inss = fields.Monetary(
        string=u"Retenção INSS", readonly=True, states=STATE)
    issqn_percent = fields.Float(u'Aliquota serviço', readonly=True, states=STATE)

    # FIX withholdings on NFSe emission
    @api.multi
    def _prepare_eletronic_invoice_values(self):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_values()
        if res.get('lista_rps'):
            res['lista_rps'][0].update({
                'valor_pis': str("%.2f" % self.valor_retencao_pis),
                'valor_cofins': str("%.2f" % self.valor_retencao_cofins),
                'valor_inss': str("%.2f" % self.valor_retencao_inss),
                'valor_ir': str("%.2f" % self.valor_retencao_irrf),
                'valor_csll' : str("%.2f" % self.valor_retencao_csll),
                'aliquota_atividade': str(float("%.2f" % self.issqn_percent) / 100),
            })
        return res

    # https://nfe.prefeitura.sp.gov.br/contribuinte/notaprint.aspx?nf=5200&inscricao=46908986&verificacao=XISVEUAB
    @api.one
    @api.depends('verify_code','numero_nfse')
    def view_nfse(self):
        if self.numero_nfse and self.verify_code:
            url = "https://nfe.prefeitura.sp.gov.br/contribuinte/notaprint.aspx?nf=%s&inscricao=46908986&verificacao=%s" % (
                self.numero_nfse, self.verify_code)
            self.nfse_url = url
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                 'target': 'self',
                'nodestroy': False,
            }
        return True

    ## This would allow to cancel if there is no NFSe issued i.e
    ## cancel a homologação NFSe
    ## bf_nfse returns super if self.model not in ('001')
    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        if self.model in ('001') and not self.numero_nfse:
            self.state = 'cancel'
            self.codigo_retorno = ''
            self.mensagem_retorno = ''
        else:
            return super(InvoiceEletronic, self).action_cancel_document(
                justificativa=justificativa)


