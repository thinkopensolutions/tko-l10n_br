# -*- coding: utf-8 -*-

from odoo import models, fields, api

class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    @api.model
    def create(self, vals):
        result = super(InvoiceEletronic, self).create(vals)
        if result.company_id:
            result.company_id.compute_annual_revenue()
        return result

    @api.multi
    def write(self, vals):
        result = super(InvoiceEletronic, self).write(vals)
        for record in self:
            record.company_id.compute_annual_revenue()
        return result