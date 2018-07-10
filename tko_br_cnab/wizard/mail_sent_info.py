# -*- coding: utf-8 -*-
# © 2017 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class MailSentInfo(models.TransientModel):
    _name = 'mail.sent.info'

    message = fields.Html(readonly =True)


    def message_ok(self):
        return True
