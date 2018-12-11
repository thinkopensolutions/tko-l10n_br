from odoo import models


class AccountTax(models.Model):
    _inherit = "account.tax"

    ## return rounded value to two digits
    ## more than two digits can caues problem in total
    ## 2500 -42.43 and 2500 -42.438 wont give same result
    def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
        result = super(AccountTax, self)._compute_amount(base_amount, price_unit, quantity=quantity, product=product,
                                                         partner=partner)
        return round(result, 2)
