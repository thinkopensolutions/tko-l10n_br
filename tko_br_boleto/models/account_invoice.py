from odoo import api, models, _
from odoo.addons.br_boleto.boleto.document import Boleto
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'



    # set nosso numero in move line
    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """ Set nosso numero on move lines, is required to export cnab even before boleto
        is generated, Nosso numero is written on the move lines only if the account is
        the same than the invoice's one.
        """
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(
            move_lines)
        for invoice in self:
            payment_mode = invoice.payment_mode_id
            if invoice.payment_mode_id:
                invoice_account_id = invoice.account_id.id
                for line in move_lines:
                    # line is a tuple (0, 0, {values})
                    if invoice_account_id == line[2]['account_id'] and payment_mode.is_boleto:

                        # compute nosso numero only for itau
                        if payment_mode.boleto_type == '6':
                            nosso_numero = str(payment_mode.nosso_numero_sequence.next_by_id()).zfill(8)
                            line[2]['nosso_numero'] = nosso_numero
                        # compute nosso numero only for Bradesco
                        if payment_mode.boleto_type == '3':
                            nosso_numero = str(payment_mode.nosso_numero_sequence.next_by_id()).zfill(11)
                            line[2]['nosso_numero'] = nosso_numero
                        # compute nosso numero only for Santander
                        if payment_mode.boleto_type == '7':
                            nosso_numero = str(payment_mode.nosso_numero_sequence.next_by_id()).zfill(13)
                            line[2]['nosso_numero'] = nosso_numero
        return move_lines
