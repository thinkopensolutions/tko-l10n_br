# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.exceptions import Warning
from datetime import date
from dateutil.relativedelta import relativedelta

class ResCompany(models.Model):
    _inherit = 'res.company'
    annual_revenue = fields.Float(
        'Faturamento Anual', required=True, #compute='compute_annual_revenue',
        digits=dp.get_precision('Account'), default=0.00,
        help=u"Faturamento Bruto dos últimos 12 meses")
    tabela_simples_nacional_id = fields.Many2one('tabela.simples.nacional', 'Tabela')
    simples_aliquota = fields.Float(compute='_get_simples_aliquota',
        string='Perc Simples', digits=dp.get_precision('Discount'), store = True)


    @api.one
    def compute_annual_revenue(self):
        # revenue within last year
        start_date = str(date.today() - relativedelta(years=1, days=1))
        invoices = self.env['invoice.eletronic'].search([('state','=','done'),('company_id','=', self.id),('data_emissao','>=', start_date),('data_emissao','<', str(date.today()))])
        self.annual_revenue = sum(invoices.mapped('valor_final'))

    @api.one
    @api.depends('annual_revenue','tabela_simples_nacional_id')
    def _get_simples_aliquota(self):
        aliquota = 0.0
        if self.fiscal_type == '1':
            annual_revenue = self.annual_revenue
            found_range = False
            for line in self.tabela_simples_nacional_id.simples_nacional_range_lines:
                if line.range_from <= annual_revenue and line.range_to >= annual_revenue:
                    found_range  = True
                    aliquota = line.aliquota
                    break
        self.simples_aliquota = aliquota
