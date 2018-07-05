from odoo import api, fields, models, tools

class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    # set default cancel message Cancelamento por erro de faturamento
    # on cancellation of eletronic invoice
    @api.multi
    def action_cancel_document(self, context=None, justificativa=u"Cancelamento por erro de faturamento"):
        return super(InvoiceEletronic, self).action_cancel_document(context = context, justificativa = justificativa)