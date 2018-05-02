# -*- encoding: utf-8 -*-
from openerp import fields, models, api

class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    irpj_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id', string=u"Regras IRPJ", domain=[('domain', '=', 'irpj')])



    def _filter_rules(self, fpos_id, type_tax, partner, product, state):
        result = super(AccountFiscalPosition, self)._filter_rules(fpos_id, type_tax, partner, product, state)
        rule_obj = self.env['account.fiscal.position.tax.rule']
        domain = [('fiscal_position_id', '=', fpos_id),
                  ('domain', '=', type_tax)]
        rules = rule_obj.search(domain)
        if rules:
            result.update({
                # IRPJ
                'tax_irpj_id': rules[0].tax_id,
            })
        return result