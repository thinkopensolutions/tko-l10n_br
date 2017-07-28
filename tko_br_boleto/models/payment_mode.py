from odoo import api, models, fields, _

class PaymentMode(models.Model):
    _inherit = "payment.mode"

    is_boleto =  fields.Boolean(u'Is Boleto')