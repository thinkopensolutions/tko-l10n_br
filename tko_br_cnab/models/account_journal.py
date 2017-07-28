# -*- coding: utf-8 -*-
# © 2017 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class AccouontJournal(models.Model):
    _inherit = "account.journal"

    cnab_return = fields.Boolean(u"Usa cobrança CNAB240?")
    cnab_journal_id = fields.Many2one("account.journal",u"Diário de Cobrança")