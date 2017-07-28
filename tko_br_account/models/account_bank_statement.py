# -*- coding: utf-8 -*-
from odoo import models, fields, api
class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    # set bank type journal of the current company
    # if context doesn't have journal_type
    @api.model
    def _default_journal(self):
        journal_type = self.env.context.get('journal_type', False)
        if not journal_type:
            journal_type = 'bank'
        company_id = self.env['res.company']._company_default_get('account.bank.statement').id
        if journal_type:
            journals = self.env['account.journal'].search(
                [('type', '=', journal_type), ('company_id', '=', company_id)])
            if journals:
                return journals[0]
        return self.env['account.journal']

    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', store=True,
                                 readonly=False,
                                 default=lambda self: self.env.user.company_id.id)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True,
                                 states={'confirm': [('readonly', True)]}, default=_default_journal)


