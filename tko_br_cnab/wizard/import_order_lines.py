# -*- coding: utf-8 -*-
# © 2017 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ImportOrderLines(models.TransientModel):
    _name = 'import.order.lines'

    start_due_date = fields.Date('Start')
    end_due_date = fields.Date('End')
    move_line_ids = fields.Many2many('account.move.line', string='Move Lines')

    def search_lines(self):
        order = self.env['payment.order'].browse(self._context.get('active_id', False))
        account_types = self.env['account.account.type'].search([('type', '=', 'receivable')]).ids
        account_ids = self.env['account.account'].search([('user_type_id', 'in', account_types)]).ids
        account_moves = self.env['account.invoice'].search([('state','=','open')]).mapped('move_id').ids
        domain = [
            ('move_id','in', account_moves),
             ('account_id', 'in', account_ids),
             ('payment_mode_id', '=', order.payment_mode_id.id),
             ('company_id', '=', order.payment_mode_id.company_id.id)]
        if self.start_due_date:
            domain.append(('date_maturity', '>=', self.start_due_date))
        if self.end_due_date:
            domain.append(('date_maturity', '<=', self.end_due_date))
        move_ids = self.env['account.move.line'].search(domain).ids

        existing_move_lines = self.env['payment.order.line'].search([('state', 'not in', ['paid'])]).mapped(
            'move_line_id').ids
        valid_move_lines = [x for x in move_ids if x not in existing_move_lines]
        self.move_line_ids = [(6, 0, valid_move_lines)]
        return {
            "type": "ir.actions.do_nothing",
        }

    def add_lines(self):
        order = self.env['payment.order'].browse(self._context.get('active_id', False))
        for move in self.move_line_ids:
            self.env['payment.order.line'].create({
                'move_line_id': move.id,
                'payment_order_id': order.id,
                'nosso_numero': move.nosso_numero,
                'payment_mode_id': move.payment_mode_id.id,
                'date_maturity': move.date_maturity,
                'value': move.amount_residual,
                'name': move.name,
            })
        return True
