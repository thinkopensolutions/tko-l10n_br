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
from odoo.exceptions import Warning



class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

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
        self.update({
            'price_subtotal': self.price_subtotal + self.valor_frete + self.valor_seguro + self.outras_despesas
        })
