# -*- encoding: utf-8 -*-
from odoo import api, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # Apply domain to show only journals from the invoice's company
    # we can't register payment on jouranls of other company
    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        result = super(AccountPayment, self)._onchange_payment_type()
        context = self._context
        if context.get('active_id', False) and context.get('active_model') == 'account.invoice':
            company_id = self.env['account.invoice'].browse(context.get('active_id')).company_id.id
            result['domain']['journal_id'].append(('company_id', '=', company_id))
        return result
