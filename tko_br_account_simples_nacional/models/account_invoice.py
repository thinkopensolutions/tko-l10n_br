# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.exceptions import Warning

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        if self.company_id.fiscal_type == '1':
            pass
        return super(AccountInvoice, self)._onchange_invoice_line_ids()

class AccountInvoiceLine(models.Model):
    _inherit= "account.invoice.line"

    simples_base_calculo = fields.Float(u"Base Simples", digits=dp.get_precision('Account'))
    simples_valor = fields.Float(u"Valor Simples",  digits=dp.get_precision('Account'))
    simples_aliquota = fields.Float(
        'Perc Simples', digits=dp.get_precision('Discount'))

    def _get_tax_amount(self):
        if not self.invoice_id.company_id:
            raise Warning(u"Company not set!")
        if not self.invoice_id.company_id.tabela_simples_nacional_id:
            raise Warning(u"Tabela simples nacional not set in company %s" %self.invoice_id.company_id.name)
        return self.invoice_id.company_id.simples_aliquota


    @api.onchange('tax_simples_id')
    def _onchange_tax_simples_id(self):
        if self.tax_simples_id:
            amount = self._get_tax_amount()
            self.simples_aliquota = amount
        self._update_invoice_line_ids()

    #add simples nacional tax
    def _update_invoice_line_ids(self):
        res = super(AccountInvoiceLine, self)._update_invoice_line_ids()
        self.invoice_line_tax_ids = self.invoice_line_tax_ids  | self.tax_simples_id

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id',
                 'invoice_id.currency_id', 'invoice_id.company_id',
                 'tax_icms_id', 'tax_icms_st_id', 'tax_icms_inter_id',
                 'tax_icms_intra_id', 'tax_icms_fcp_id', 'tax_ipi_id',
                 'tax_pis_id', 'tax_cofins_id', 'tax_ii_id', 'tax_issqn_id',
                 'incluir_ipi_base', 'tem_difal', 'icms_aliquota_reducao_base',
                 'ipi_reducao_bc', 'icms_st_aliquota_mva', 'tax_simples_id',
                 'icms_st_aliquota_reducao_base', 'icms_aliquota_credito',
                 'icms_st_aliquota_deducao')
    def _compute_price(self):
        super(AccountInvoiceLine, self)._compute_price()
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)

        valor_bruto = self.price_unit * self.quantity
        desconto = valor_bruto * self.discount / 100.0
        subtotal = valor_bruto - desconto

        taxes = False
        self._update_invoice_line_ids()
        if self.invoice_line_tax_ids:
            ctx = self._prepare_tax_context()

            tax_ids = self.invoice_line_tax_ids.with_context(**ctx)

            taxes = tax_ids.with_context(company_id=self.invoice_id.company_id).compute_all(
                price, currency, self.quantity, product=self.product_id,
                partner=self.invoice_id.partner_id)
        simples = ([x for x in taxes['taxes']
                    if x['id'] == self.tax_simples_id.id]) if taxes else []

        self.update({
            'simples_base_calculo': sum([x['base'] for x in simples]),
            'simples_valor': sum([x['amount'] for x in simples]),
        })
