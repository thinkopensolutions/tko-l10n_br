# -*- coding: utf-8 -*-
# © 2017 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api

class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    # set order line to Enviado
    @api.multi
    def send_mail_action(self):
        context = self._context
        result = super(MailComposeMessage, self).send_mail_action()
        if context.get('payment_order_line', False) and context.get('order_line_id', False):
            line = self.env['payment.order.line'].browse(context.get('order_line_id'))
            line.state = 'e'
        return result