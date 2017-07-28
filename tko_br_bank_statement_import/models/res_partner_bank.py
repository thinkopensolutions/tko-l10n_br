
from odoo import  models, api
import re

def sanitize_account_number(acc_number):
    if acc_number:
        return re.sub(r'\W+', '', acc_number).upper()
    return False

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    # sanitize account number in brazilian format
    @api.depends('acc_number','bra_number','acc_number_dig','bra_number_dig')
    def _compute_sanitized_acc_number(self):
        for bank in self:
            acc_number = "%s-%s-%s-%s" % (
            self.bra_number or '', self.bra_number_dig or '', self.acc_number or '', self.acc_number_dig or '')
            bank.sanitized_acc_number = sanitize_account_number(acc_number)
