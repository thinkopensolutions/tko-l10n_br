# -*- coding: utf-8 -*-
from openerp import fields, models, api


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    @api.model
    def create(self, vals):
        res = super(InvoiceEletronic, self).create(vals)
        if res.company_id.issue_eletronic_doc != 'm':
            res.action_send_eletronic_invoice()
        return res