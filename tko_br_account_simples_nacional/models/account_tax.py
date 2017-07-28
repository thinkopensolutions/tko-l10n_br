
from  odoo import models, api
import math

class AccountTax(models.Model):
    _inherit = "account.tax"

    def _compute_simples(self, price_base):
        simples_tax = self.filtered(lambda x: x.domain == 'simples')
        if not simples_tax:
            return []
        taxes = []
        for tax in simples_tax:
            vals = self._tax_vals(tax)
            vals['amount'] = tax._compute_amount_simples(price_base, 1.0)
            vals['base'] = price_base
            taxes.append(vals)
        return taxes

    def _compute_amount_simples(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
        """ Returns the amount of a single tax. base_amount is the actual amount on which the tax is applied, which is
            price_unit * quantity eventually affected by previous taxes (if tax is include_base_amount XOR price_include)
        """
        context = self.env.context
        company = context.get('company_id')
        self.ensure_one()
        if company:
            amount = company.simples_aliquota
        else:
            amount = 0.0
        return base_amount *  amount / 100