# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    ThinkOpen Solutions Brasil
#    Copyright (C) Thinkopen Solutions <http://www.tkobr.com>.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import openerp
from openerp import SUPERUSER_ID
from openerp import fields, models, api
from odoo.addons import decimal_precision as dp
import math


class AccountTax(models.Model):
    _inherit = 'account.tax'

    withholding_type = fields.Selection([('percent', 'Percent'), ('fixed', 'Fixed')], string='Type', default='percent',
                                        required=True)
    withholding_amount = fields.Float(digits=dp.get_precision('Account'), string=u'Amount',
                                      help="For taxes of type percentage, enter % ratio between 0-1.")

    # FIX total_excluded computation
    @api.multi
    def compute_all(self, price_unit, currency=None, quantity=1.0,
                    product=None, partner=None):

        exists_br_tax = len(self.filtered(lambda x: x.domain)) > 0
        if not exists_br_tax:
            res = super(AccountTax, self).compute_all(
                price_unit, currency, quantity, product, partner)
            res['price_without_tax'] = round(price_unit * quantity, 2)
            return res

        price_base = price_unit * quantity
        ipi = self._compute_ipi(price_base)
        icms = self._compute_icms(
            price_base,
            ipi[0]['amount'] if ipi else 0.0)
        icmsst = self._compute_icms_st(
            price_base,
            ipi[0]['amount'] if ipi else 0.0,
            icms[0]['amount'] if icms else 0.0)
        difal = self._compute_difal(
            price_base, ipi[0]['amount'] if ipi else 0.0)
        simples = self._compute_simples(price_base)
        pis_cofins = self._compute_pis_cofins(price_base)
        issqn = self._compute_issqn(price_base)
        ii = self._compute_ii(price_base)
        irpj = self._compute_irpj(price_base)
        csll = self._compute_csll(price_base)
        taxes = icms + icmsst + simples + difal + ipi + pis_cofins + issqn + ii + irpj + csll

        total_included = total_excluded = price_base
        for tax in taxes:
            tax_id = self.filtered(lambda x: x.id == tax['id'])
            # subtract if tax is to discount
            # else add the value
            if tax_id.tax_discount:
                total_excluded -= tax['amount']

        return {
            'taxes': sorted(taxes, key=lambda k: k['sequence']),
            'total_excluded': total_excluded,
            'total_included': total_included,
            'base': price_base,
        }

    # compute withholding base amount
    def _compute_amount_withholding(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
        """ Returns the amount of a single tax. base_amount is the actual amount on which the tax is applied, which is
            price_unit * quantity eventually affected by previous taxes (if tax is include_base_amount XOR price_include)
        """
        self.ensure_one()
        if self.withholding_type == 'fixed':
            # Use copysign to take into account the sign of the base amount which includes the sign
            # of the quantity and the sign of the price_unit
            # Amount is the fixed price for the tax, it can be negative
            # Base amount included the sign of the quantity and the sign of the unit price and when
            # a product is returned, it can be done either by changing the sign of quantity or by changing the
            # sign of the price unit.
            # When the price unit is equal to 0, the sign of the quantity is absorbed in base_amount then
            # a "else" case is needed.
            if base_amount:
                return math.copysign(quantity, base_amount) * self.withholding_amount
            else:
                return quantity * self.withholding_amount
        if (self.withholding_type == 'percent' and not self.price_include):
            return base_amount * self.withholding_amount / 100
        if self.withholding_type == 'percent' and self.price_include:
            return base_amount - (base_amount / (1 + self.withholding_amount / 100))

    # compute withholdings
    @api.multi
    def compute_all_withholding(self, price_unit, currency=None, quantity=1.0, product=None, partner=None):
        """ Returns all information required to apply taxes (in self + their children in case of a tax goup).
            We consider the sequence of the parent for group of taxes.
                Eg. considering letters as taxes and alphabetic order as sequence :
                [G, B([A, D, F]), E, C] will be computed as [A, D, F, C, E, G]

        RETURN: {
            'total_excluded': 0.0,    # Total without taxes
            'total_included': 0.0,    # Total with taxes
            'taxes': [{               # One dict for each tax in self and their children
                'id': int,
                'name': str,
                'amount': float,
                'sequence': int,
                'account_id': int,
                'refund_account_id': int,
                'analytic': boolean,
            }]
        } """
        if len(self) == 0:
            company_id = self.env.user.company_id
        else:
            company_id = self[0].company_id
        if not currency:
            currency = company_id.currency_id
        taxes = []
        prec = currency.decimal_places
        round_tax = False if company_id.tax_calculation_rounding_method == 'round_globally' else True
        round_total = True
        if 'round' in self.env.context:
            round_tax = bool(self.env.context['round'])
            round_total = bool(self.env.context['round'])

        if not round_tax:
            prec += 5
        base_values = self.env.context.get('base_values')
        if not base_values:
            total_excluded = total_included = base = round(price_unit * quantity, prec)
        else:
            total_excluded, total_included, base = base_values
        for tax in self.sorted(key=lambda r: r.sequence):

            tax_amount = tax._compute_amount_withholding(base, price_unit, quantity, product, partner)
            if not round_tax:
                tax_amount = round(tax_amount, prec)
            else:
                tax_amount = currency.round(tax_amount)

            if tax.price_include:
                total_excluded -= tax_amount
                base -= tax_amount
            else:
                total_included += tax_amount

            # Keep base amount used for the current tax
            tax_base = base

            if tax.include_base_amount:
                base += tax_amount

            taxes.append({
                'id': tax.id,
                'name': tax.with_context(**{'lang': partner.lang} if partner else {}).name,
                'amount': tax_amount,
                'base': tax_base,
                'sequence': tax.sequence,
                'account_id': tax.account_id.id,
                'refund_account_id': tax.refund_account_id.id,
                'analytic': tax.analytic,
            })
        return {
            'taxes': sorted(taxes, key=lambda k: k['sequence']),
            'total_excluded': currency.round(total_excluded) if round_total else total_excluded,
            'total_included': currency.round(total_included) if round_total else total_included,
            'base': base,
        }