# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    Thinkopen Brasil
#    Copyright (C) Thinkopen Solutions Brasil (<http://www.tkobr.com>).
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
from odoo import fields, models


class product_template(models.Model):
	_inherit = 'product.template'
	
	is_dangerous = fields.Boolean(u'Produto Perigoso')
	net_weight = fields.Float(u'Peso Unitário Líquido ')
	sub_type = fields.Selection([('0',u'Veículos'),('1',u'Medicamentos'),('3',u'Armamentos'),('4',u'Combustível'),('5',u'serviço')], string='Sub Tipo')
	
	_defaults = {
	'type' : 'product'
	}
	
class product_category(models.Model):
	_inherit = 'product.category'
	
	company_id = fields.Many2one('res.company',string='Company', required=True, default=lambda self: self.env.user.company_id)
