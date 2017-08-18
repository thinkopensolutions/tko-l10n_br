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
import openerp.addons.decimal_precision as dp
from openerp import fields, models, api


class WithholdingTaxLine(models.Model):
    _name = 'withholding.tax.line'

    invoice_id = fields.Many2one('account.invoice', string='Invoice Line',
                                 ondelete='cascade', index=True)
    name = fields.Char(string='Tax Description',
                       required=True)
    account_id = fields.Many2one('account.account', string='Tax Account',
                                 required=True, domain=[('type', 'not in', ['view', 'income', 'closed'])])
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic account')
    base = fields.Float(string='Base', digits=dp.get_precision('Account'))
    amount = fields.Float(string='Amount', digits=dp.get_precision('Account'))
    manual = fields.Boolean(string='Manual', default=True)
    sequence = fields.Integer(string='Sequence',
                              help="Gives the sequence order when displaying a list of invoice tax.")

    base_amount = fields.Float(string='Base Code Amount', digits=dp.get_precision('Account'),
                               default=0.0)
    tax_amount = fields.Float(string='Tax Code Amount', digits=dp.get_precision('Account'),
                              default=0.0)

    company_id = fields.Many2one('res.company', string='Company',
                                 related='account_id.company_id', store=True, readonly=True)
    tax_id = fields.Many2one('account.tax', string='Tax', ondelete='restrict')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_tax_withholding = fields.Float(compute='get_amount_tax_withholding', string='Retenções ( - ) ',
                                          digits=dp.get_precision('Account'), store=True)
    withholding_tax_lines = fields.One2many('withholding.tax.line', 'invoice_id', string=u'Retenções', copy=True)
    amount_total_liquid = fields.Float(compute='_compute_amount', string=u'Líquido', store= True)

    # correct the price in account move line
    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        contador = 0
        for line in self.invoice_line_ids:
            #price_total : (qty * unit_price) - discount
            res[contador]['price'] = line.price_total
            contador += 1

        return res


    # include deduction value in tax account move
    # applicable only for customer invoices
    # create account moves for withholding taxes
    @api.model
    def tax_line_move_line_get(self):
        res = super(AccountInvoice, self).tax_line_move_line_get()
        if self.type == 'out_invoice':
            for line in res:
                if line.get('price') < 0 and line.get('invoice_id', False) and line.get('name', False):
                    withholding_line = self.env['withholding.tax.line'].search([('invoice_id','=', line['invoice_id']), ('name','=',line['name'])])
                    if len(withholding_line) > 1:
                        raise Warning("Multiple withholding lines found !!")
                    line['price'] = line['price']# - withholding_line.amount
            done_taxes = []
            for tax_line in sorted(self.withholding_tax_lines, key=lambda x: -x.sequence):
                if tax_line.amount:
                    tax = tax_line.tax_id
                    if tax.amount_type == "group":
                        for child_tax in tax.children_tax_ids:
                            done_taxes.append(child_tax.id)
                    done_taxes.append(tax.id)
                    res.append({
                        'invoice_tax_line_id': tax_line.id,
                        'tax_line_id': tax_line.tax_id.id,
                        'type': 'tax',
                        'name': tax_line.name,
                        'price_unit': tax_line.amount,
                        'quantity': 1,
                        'price': tax_line.amount * -1,
                        'account_id': tax_line.account_id.id,
                        'account_analytic_id': tax_line.account_analytic_id.id,
                        'invoice_id': self.id,
                        'tax_ids': [(6, 0, done_taxes)] if tax_line.tax_id.include_base_amount else []
                    })
        return res


    # return total of invoice don't compute from move lines
    # it is used as 1st account move in journal entry
    @api.multi
    def compute_invoice_totals(self, company_currency, invoice_move_lines):
        total, total_currency, invoice_move_lines = super(AccountInvoice, self).compute_invoice_totals(company_currency,
                                                                               invoice_move_lines)
        sign = 1
        if self.type in ('in_invoice', 'out_refund'):
            sign = -1
        total = self.amount_total * sign
        return total, total_currency, invoice_move_lines

    # FIX total of invoice
    @api.one
    @api.depends('invoice_line_ids.price_subtotal',
                 'tax_line_ids.amount',
                 'currency_id', 'company_id')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        amount_tax_with_tax_discount = sum(tax.amount for tax in self.tax_line_ids if tax.tax_id.tax_discount)

        amount_tax_without_tax_discount = sum(tax.amount for tax in self.tax_line_ids if not tax.tax_id.tax_discount) \
                                          - sum(
            tax.amount for tax in self.withholding_tax_lines if not tax.tax_id.tax_discount)
        self.total_tax = sum(l.amount for l in self.tax_line_ids) - sum(l.amount for l in self.withholding_tax_lines)
        self.amount_total = self.total_bruto - self.total_desconto + amount_tax_without_tax_discount - self.amount_tax_withholding
        self.amount_total_liquid = self.total_bruto - self.total_desconto - amount_tax_with_tax_discount - self.amount_tax_withholding

    # compute Tax Lines in invoice without withholdings
    # @api.multi
    # def get_taxes_values(self):
    #     tax_values = super(AccountInvoice, self).get_taxes_values()
    #     withholding_tax_values = self.get_withholding_taxes_values()
    #     # for key, value in tax_values.items():
    #     #     if withholding_tax_values.get(key):
    #     #         tax_values[key].update({'amount': tax_values[key]['amount']})
    #     #         #tax_values[key].update({'amount': tax_values[key]['amount'] - withholding_tax_values[key]['amount']})
    #     return tax_values

    # create withholding lines on change event
    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        result = super(AccountInvoice, self)._onchange_invoice_line_ids()
        taxes_grouped = self.get_withholding_taxes_values()
        withholding_tax_lines = self.withholding_tax_lines.browse([])
        for tax in taxes_grouped.values():
            withholding_tax_lines += withholding_tax_lines.new(tax)
        self.withholding_tax_lines = withholding_tax_lines
        return

    # compute Withholdings and Liquid amount
    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'withholding_tax_lines.amount')
    def get_amount_tax_withholding(self):
        total_withholding = 0.0
        for line in self.withholding_tax_lines:
            total_withholding += line.amount
        self.amount_tax_withholding = total_withholding

    @api.multi
    def get_withholding_taxes_values(self):
        tax_grouped = {}
        for line in self.invoice_line_ids:
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.invoice_line_tax_ids.compute_all_withholding(price_unit, self.currency_id, line.quantity,
                                                                      line.product_id,
                                                                      self.partner_id)['taxes']
            for tax in taxes:
                if tax.get('amount'):
                    val = self._prepare_tax_line_vals(line, tax)
                    key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                    if key not in tax_grouped:
                        tax_grouped[key] = val
                    else:
                        tax_grouped[key]['amount'] += val['amount']
                        tax_grouped[key]['base'] += val['base']
        return tax_grouped

    @api.multi
    def compute_taxes(self):
        result = super(AccountInvoice, self).compute_taxes()
        """Function used in other module to compute the taxes on a fresh invoice created (onchanges did not applied)"""
        account_withholding_tax = self.env['withholding.tax.line']
        for invoice in self:
            # Delete non-manual tax lines
            self._cr.execute("DELETE FROM WithholdingTaxLine WHERE invoice_id=%s AND manual is False", (invoice.id,))
            self.invalidate_cache()

            # Generate one tax line per tax, however many invoice lines it's applied to
            tax_grouped_withholdings = invoice.get_withholding_taxes_values()

            # Create new tax lines
            for tax in tax_grouped_withholdings.values():
                account_withholding_tax.create(tax)
        return result
