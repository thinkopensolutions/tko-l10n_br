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

    numero_nfse = fields.Char(
        string=u"Número NFSe", size=50, compute='_get_numero_nfse')
    amount_tax_withholding = fields.Float(compute='get_amount_tax_withholding', string='Retenções ( - ) ',
                                          digits=dp.get_precision('Account'), store=True)
    withholding_tax_lines = fields.One2many('withholding.tax.line', 'invoice_id', string=u'Retenções', copy=True)
    amount_total_liquid = fields.Float(compute='_compute_amount', string=u'Líquido', store=True)

    # set Analytic Account from Tax instead of invoice line
    def _prepare_tax_line_vals(self, line, tax):
        # check if the tax is withholding or normal
        withholding = tax.get('withholding', False)
        result = super(AccountInvoice, self)._prepare_tax_line_vals(line, tax)
        if 'id' in tax.keys() and tax['analytic']:
            tax = self.env['account.tax'].browse(tax['id'])
            result.update({'account_analytic_id' : tax.withholding_analytic_id.id if withholding else tax.analytic_id.id})
        return result

    @api.one
    def _get_numero_nfse(self):
        edoc = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', self.id), ('state', '=', 'done')], limit=1)
        if len(edoc):
            self.numero_nfse = edoc.numero_nfse


    # include deduction value in tax account move
    # applicable only for customer invoices
    # create account moves for withholding taxes
    @api.model
    def tax_line_move_line_get(self):
        res = super(AccountInvoice, self).tax_line_move_line_get()
        if self.type == 'out_invoice':
            for line in res:
                if line.get('price') < 0 and line.get('invoice_id', False) and line.get('name', False):
                    withholding_line = self.env['withholding.tax.line'].search(
                        [('invoice_id', '=', line['invoice_id']), ('name', '=', line['name'])])
                    if len(withholding_line) > 1:
                        raise Warning("Multiple withholding lines found !!")
                    line['price'] = line['price']  # - withholding_line.amount
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
                 'withholding_tax_lines.amount',
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

        # Retenções
        lines = self.invoice_line_ids
        self.issqn_retention = sum(l.issqn_valor_retencao for l in lines)
        self.pis_retention = sum(l.pis_valor_retencao for l in lines)
        self.cofins_retention = sum(l.cofins_valor_retencao for l in lines)
        self.csll_retention = sum(l.csll_valor_retencao for l in lines)
        self.irrf_retention = sum(l.irrf_valor_retencao for l in lines)
        self.inss_retention = sum(l.inss_valor_retencao for l in lines)

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
                    tax['withholding'] = True
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
            self._cr.execute("DELETE FROM withholding_tax_line WHERE invoice_id=%s AND manual is False", (invoice.id,))
            self.invalidate_cache()

            # Generate one tax line per tax, however many invoice lines it's applied to
            tax_grouped_withholdings = invoice.get_withholding_taxes_values()

            # Create new tax lines
            for tax in tax_grouped_withholdings.values():
                account_withholding_tax.create(tax)
        return result


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    icms_valor_retencao = fields.Float(
        'Valor ICMS Retenção', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_st_valor_retencao = fields.Float(
        'Valor ICMSST Retenção', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00)

    ipi_valor_retencao = fields.Float(
        'Valor IPI Retenção', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00)
    pis_valor_retencao = fields.Float(
        'Valor PIS Retenção', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00)
    cofins_valor_retencao = fields.Float(
            'Valor COFINS Retenção', required=True, compute='_compute_price', store=True,
            digits=dp.get_precision('Account'), default=0.00)
    issqn_valor_retencao = fields.Float(
            'Valor ISSQN Retenção', required=True, compute='_compute_price', store=True,
            digits=dp.get_precision('Account'), default=0.00)
    irpj_valor_retencao = fields.Float(
                'Valor IRPJ Retenção', required=True, compute='_compute_price', store=True,
                digits=dp.get_precision('Account'), default=0.00)
    ii_valor_retencao = fields.Float(
                    'Valor II Retenção', required=True, compute='_compute_price', store=True,
                    digits=dp.get_precision('Account'), default=0.00)
    csll_valor_retencao = fields.Float(
                        'Valor CSLL Retenção', required=True, compute='_compute_price', store=True,
                        digits=dp.get_precision('Account'), default=0.00)
    irrf_valor_retencao = fields.Float(
                            'Valor IRRF Retenção', required=True, compute='_compute_price', store=True,
                            digits=dp.get_precision('Account'), default=0.00)
    inss_valor_retencao = fields.Float(
                                'Valor INSS Retenção', required=True, compute='_compute_price', store=True,
                                digits=dp.get_precision('Account'), default=0.00)

    is_cust_invoice = fields.Boolean(string='Is Customer Invoice', default=False)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.invoice_id.type == 'out_invoice':
            self.is_cust_invoice = True
        if self.invoice_id.type == 'in_invoice':
            if self.product_id:
                self.is_cust_invoice = False
        return super(AccountInvoiceLine, self)._onchange_product_id()

    def _set_taxes(self):
        res = super(AccountInvoiceLine, self)._set_taxes()
        if self.product_id.taxes_id:
            for tax in self.product_id.taxes_id:
                if tax.domain:
                    self.update({'tax_%s_id' % tax.domain: tax.id})
        return res

    ## Compute retençoẽs in Invoice Line
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id',
                 'invoice_id.currency_id', 'invoice_id.company_id',
                 'tax_icms_id', 'tax_icms_st_id', 'tax_icms_inter_id',
                 'tax_icms_intra_id', 'tax_icms_fcp_id', 'tax_ipi_id',
                 'tax_pis_id', 'tax_cofins_id', 'tax_ii_id', 'tax_issqn_id',
                 'tax_irpj_id',
                 'tax_csll_id', 'tax_irrf_id', 'tax_inss_id',
                 'incluir_ipi_base', 'tem_difal', 'icms_aliquota_reducao_base',
                 'ipi_reducao_bc', 'icms_st_aliquota_mva', 'tax_simples_id',
                 'icms_st_aliquota_reducao_base', 'icms_aliquota_credito',
                 'icms_st_aliquota_deducao', 'icms_st_base_calculo_manual',
                 'icms_base_calculo_manual', 'ipi_base_calculo_manual',
                 'pis_base_calculo_manual', 'cofins_base_calculo_manual',
                 'icms_st_aliquota_deducao', 'ii_base_calculo')
    def _compute_price(self):
        super(AccountInvoiceLine, self)._compute_price()
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        if self.invoice_line_tax_ids:
            ctx = self._prepare_tax_context()

            tax_ids = self.invoice_line_tax_ids.with_context(**ctx)

            taxes = tax_ids.compute_all_withholding(
                price, currency, self.quantity, product=self.product_id,
                partner=self.invoice_id.partner_id)['taxes']

            icms_valor_retencao = ([x for x in taxes
                                    if x['id'] == self.tax_icms_id.id]) if taxes else []
            icms_st_valor_retencao = ([x for x in taxes
                                      if x['id'] == self.tax_icms_st_id.id]) if taxes else []
            ipi_valor_retencao = ([x for x in taxes
                                   if x['id'] == self.tax_ipi_id.id]) if taxes else []
            pis_valor_retencao = ([x for x in taxes
                                   if x['id'] == self.tax_pis_id.id]) if taxes else []
            cofins_valor_retencao = ([x for x in taxes
                                      if x['id'] == self.tax_cofins_id.id]) if taxes else []
            issqn_valor_retencao = ([x for x in taxes
                                     if x['id'] == self.tax_issqn_id.id]) if taxes else []

            irpj_valor_retencao = ([x for x in taxes
                                    if x['id'] == self.tax_irpj_id.id]) if taxes else []
            ii_valor_retencao = ([x for x in taxes
                                  if x['id'] == self.tax_ii_id.id]) if taxes else []
            csll_valor_retencao = ([x for x in taxes
                                    if x['id'] == self.tax_csll_id.id]) if taxes else []
            irrf_valor_retencao = ([x for x in taxes
                                    if x['id'] == self.tax_irrf_id.id]) if taxes else []
            inss_valor_retencao = ([x for x in taxes
                                    if x['id'] == self.tax_inss_id.id]) if taxes else []

            self.update({'pis_valor_retencao': sum([x['amount'] for x in pis_valor_retencao]),
                         'icms_valor_retencao': sum([x['amount'] for x in icms_valor_retencao]),
                         'icms_st_valor_retencao': sum([x['amount'] for x in icms_st_valor_retencao]),
                         'cofins_valor_retencao': sum([x['amount'] for x in cofins_valor_retencao]),
                         'issqn_valor_retencao': sum([x['amount'] for x in issqn_valor_retencao]),
                         'irpj_valor_retencao': sum([x['amount'] for x in irpj_valor_retencao]),
                         'ii_valor_retencao': sum([x['amount'] for x in ii_valor_retencao]),
                         'csll_valor_retencao': sum([x['amount'] for x in csll_valor_retencao]),
                         'irrf_valor_retencao': sum([x['amount'] for x in irrf_valor_retencao]),
                         'ipi_valor_retencao': sum([x['amount'] for x in ipi_valor_retencao]),
                         'inss_valor_retencao': sum([x['amount'] for x in inss_valor_retencao]),
                         })


