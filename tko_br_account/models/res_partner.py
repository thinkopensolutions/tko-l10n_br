# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.depends('is_company', 'parent_id.commercial_partner_id')
    def _compute_commercial_partner(self):
        for partner in self:
            partner.commercial_partner_id = partner
