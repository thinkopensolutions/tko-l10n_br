# -*- encoding: utf-8 -*-
from openerp import fields, models, api
from odoo.exceptions import Warning


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_edoc_vals(self, invoice):
        vals = super(AccountInvoice, self)._prepare_edoc_vals(invoice)

        vals.update({'issqn_percent': invoice.invoice_line_ids[
            0].issqn_percent})  ## can be taken form the 1st line because it is unique per eletronic invoice
        return vals

    def _prepare_edoc_item_vals(self, line):
        result = super(AccountInvoice, self)._prepare_edoc_item_vals(line)
        result.update({
            'pis_valor_retencao': abs(line.pis_valor_retencao),
            'cofins_valor_retencao': abs(line.cofins_valor_retencao),
            'issqn_valor_retencao': abs(line.issqn_valor_retencao),
            'irrf_valor_retencao': abs(line.irrf_valor_retencao),
            'inss_valor_retencao': abs(line.inss_valor_retencao),

        })
        return result


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    issqn_percent = fields.Float(u'Aliquota serviço')

    def get_issqn(self, issqn_percent=0.0):
        company = self.company_id
        if not company:
            company = self.invoice_id.company_id
        if company:
            taxes = self.env['account.tax'].search(
                [('domain', '=', 'issqn'), ('company_id', '=', company.id), ('amount', '=', issqn_percent)])
        return taxes

    @api.onchange('product_id')
    def _br_account_onchange_product_id(self):
        super(AccountInvoiceLine, self)._br_account_onchange_product_id()
        taxes = self.get_issqn(self.product_id.service_type_id.issqn_percent)
        self.tax_issqn_id = taxes and taxes[0].id
