# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.exceptions import Warning


class SimplesNacionalRange(models.Model):
    _name = "simples.nacional.range"

    range_from = fields.Float(u"From")
    range_to = fields.Float(u"To")
    aliquota = fields.Float(u"Aliquot (%)")
    tabela_id = fields.Many2one('tabela.simples.nacional', 'Tabela')

    @api.constrains
    def range_check(self):
        if self.range_from < self.range_to:
            raise Warning("Range from can not be greater than range to")

class TabelaSimplesNacional(models.Model):
    _name = "tabela.simples.nacional"

    name = fields.Char(u"Name", required=True)
    simples_nacional_range_lines = fields.One2many('simples.nacional.range', 'tabela_id', string="Tablea", required=True)
