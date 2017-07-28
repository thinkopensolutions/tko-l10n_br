# -*- coding: utf-8 -*-
# © 2017 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.exceptions import Warning
import base64
from datetime import datetime


class PaymentMode(models.Model):
    _inherit = "payment.mode"

    email_template_id = fields.Many2one("mail.template", "Email Template")
    writeoff_account_id = fields.Many2one("account.account", u"Write off account")


class PaymentOrder(models.Model):
    _inherit = "payment.order"

    @api.multi
    def validar_cnab(self):
        for order in self:
            context = self.env.context
            # Export only open lines
            if 'export_open_lines' in context.keys():
                if not 'r' in order.line_ids.mapped('state'):
                    raise Warning("No line to export")
        return super(PaymentOrder, self).validar_cnab()

    # send mass mail
    @api.multi
    def send_all_boletos(self):

        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        try:
            template = self.payment_mode_id.email_template_id
            template_id = template.id
        except ValueError:
            template_id = False
        message = '''<p><strong>Boletos enviados com sucesso!</strong></p>'''
        warn = False
        for line in self.line_ids:
            vencimento = fields.Date.from_string(line.move_line_id.date_maturity)
            # if vencimento is smaller than today and line is not set to reconciled
            # Boleto report is not generated
            if vencimento and vencimento > datetime.today().date() and line.move_line_id.invoice_id.date_invoice:
                if line.move_line_id and line.move_line_id.date_maturity:
                    if line.state == 'a' and line.partner_id:
                        composer = self.env['mail.compose.message'].with_context({
                            'default_composition_mode': 'comment',
                            'default_model': 'account.move.line',
                            'default_res_id': line.move_line_id.id,
                            'default_use_template': False,
                            'default_template_id': False,
                            'active_ids': [line.move_line_id.id],
                            'origin_model': 'account.move.line',
                        }).create({'subject': 'Demo Subject', 'body': 'Dummy body'})

                        values = \
                            composer.onchange_template_id(template_id, 'comment', 'account.move.line',
                                                          line.move_line_id.id)[
                                'value']
                        # use _convert_to_cache to return a browse record list from command list or id list for x2many fields
                        #values = composer._convert_to_record(composer._convert_to_cache(values))
                        #values['attachment_ids'] = [(6, 0, values['attachment_ids'].ids)]
                        # update partner in email
                        values['partner_ids'] = [(6, 0, [line.partner_id.id])]
                        composer.write(values)
                        composer.send_mail_action()
                        # set state to Enviado
                        line.state = 'e'
            else:
                warn = True
        if warn:
            message = '''
            <p><strong>Quase todos os boletos foram enviados com sucessos</strong>!</p>
    <p>&nbsp;</p>
    <p>As raz&otilde;es poss&iacute;veis para o n&atilde;o envio dos boletos abaixo s&atilde;o:</p>
    <ul>
    <li>Data de vencimento menor que %s ;</li>
    <li>Data de vencimento n&atilde;o preenchida</li>
    <li>Fatura n&atilde;o confirmada</li>
    </ul>
            
            ''' % fields.date.today()

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.sent.info',
            'target': 'new',
            'context': {'default_message': message}
        }


class PaymentOrderLine(models.Model):
    _inherit = "payment.order.line"

    cnab_lines = fields.One2many("cnab.lines", 'cnab_line_id', string="CNAB Lines")
    error_message = fields.Char("Message", compute="_get_error_message")
    return_move_id = fields.Many2one("account.move", u"Return Move")
    date_aguardando = fields.Date('Data Aguardando')
    date_enviado = fields.Date('Data Enviado')

    # set Data Aguardando and Data Enviado
    @api.multi
    def write(self, vals):
        if vals.get('state'):
            state = vals.get('state')
            if state == 'e':
                vals.update({'date_enviado': datetime.today()})
            if state == 'ag':
                vals.update({'date_aguardando': datetime.today()})
        return super(PaymentOrderLine, self).write(vals)

    @api.one
    def _get_error_message(self):
        for line in self.cnab_lines:
            self.error_message = line.servico_codigo_movimento
            break

    @api.one
    def cancel_line(self):
        self.state = 'c'

    @api.one
    def reset_line(self):
        self.state = 'r'

    @api.multi
    def send_boleto(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = self.payment_order_id.payment_mode_id.email_template_id.id
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        res_id = self.move_line_id.id
        partner_ids = []
        if self.partner_id:
            partner_ids.append(self.partner_id.id)
        ctx.update({
            'default_model': 'account.move.line',
            'default_res_id': res_id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'active_ids': [res_id],
            'origin_model': 'account.move.line',
            'default_partner_ids': [(6, 0, partner_ids)],
            'payment_order_line': True,
            'order_line_id': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class CnabLines(models.Model):
    """  """
    _name = 'cnab.lines'

    # date, name, type , error showing only 4 columns in tree view
    name = fields.Char(string="Name", required=False, )
    account_no = fields.Char('Account No')
    amount = fields.Float('Amount')
    ref = fields.Char('Reference')
    date = fields.Date('Date')
    error_message = fields.Char("Error Message")
    partner_id = fields.Many2one('res.partner', 'Partner')
    unique_import_id = fields.Char('Unique Import ID')
    transaction_id = fields.Char('Transaction ID')
    cnab_line_id = fields.Many2one('payment.order.line', 'Order Line')
    servico_codigo_movimento = fields.Char("Servico Codigo")
