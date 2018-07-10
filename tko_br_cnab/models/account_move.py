# -*- coding: utf-8 -*-
# © 2017 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class AccouontMove(models.Model):
    _inherit = "account.move"

    # unlink payment order lines linked with this move
    @api.multi
    def unlink(self):
        for record in self:
            self.env['payment.order.line'].search([('move_id', '=', record.id)]).unlink()
        return super(AccouontMove, self).unlink()

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def message_get_reply_to(self, res_ids, default=None):
        """ Override to get the reply_to of the parent project. """
        move_lines = self.sudo().browse(res_ids)
        invoice_ids = move_lines.mapped('invoice_id').ids
        aliases = self.env['account.invoice'].message_get_reply_to(invoice_ids, default=default)
        return {line.id: aliases.get(line.invoice_id.id, False) for line in move_lines}