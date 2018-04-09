# -*- coding: utf-8 -*-
# © 2017 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields
from cnab_explicit_errors import service_codigo_message, table_1, table_2, table_3, table_4, table_5
from datetime import date
from odoo.exceptions import Warning
import logging

_logger = logging.getLogger(__name__)


class AccountBankStatementImport(models.TransientModel):
    """  """
    _inherit = 'account.bank.statement.import'

    # fix constraint to check account number
    # sometimes we get full account with agency and digit and sometimes only account number
    def _check_journal_bank_account(self, journal, account_number):
        return journal.bank_account_id.sanitized_acc_number == account_number or journal.bank_account_id.acc_number == account_number

    # TODO
    # commented unused code wrote for auto reconciliation
    # @api.model
    # def move_lines_get(self, line, journal, amount_paid, statement_id):
    #     if statement_id and len(statement_id):
    #         statement_id = statement_id[0]
    #     else:
    #         statement_id = False
    #     write_off_amount = amount_paid - float(line.value)
    #     if not line.payment_order_id.payment_mode_id.writeoff_account_id:
    #         raise Warning(u"Writeoff acount not set in payment mode in %s" %(line.payment_order_id.payment_mode_id and line.payment_order_id.payment_mode_id.name))
    #     move_lines = []
    #     # Debit entry
    #     move_lines.append((0, 0, {
    #         'name': "TESTE",
    #         'account_id': journal.default_debit_account_id.id,
    #         'partner_id': line.partner_id.id,
    #         'debit': amount_paid,
    #         'credit': 0,
    #         'company_id': journal and journal.company_id.id,
    #         'statement_id': statement_id,
    #     }))
    #     # Credit entry
    #     move_lines.append((0, 0, {
    #         'name': "TESTE",
    #         'account_id': line.move_line_id.account_id.id,
    #         'partner_id': line.partner_id.id,
    #         'debit': 0,
    #         'credit': amount_paid - write_off_amount,
    #         'company_id': journal and journal.company_id.id,
    #         'statement_id': statement_id,
    #     }))
    #     # create writeoffs
    #     if write_off_amount < 0:
    #         # debit entry
    #         move_lines.append((0, 0, {
    #             'name': "TESTE",
    #             'account_id': line.payment_order_id.payment_mode_id.writeoff_account_id.id,
    #             'partner_id': line.partner_id.id,
    #             'debit': abs(write_off_amount),
    #             'credit': 0,
    #             'company_id': journal and journal.company_id.id,
    #             'statement_id': statement_id,
    #         }))
    #     if write_off_amount > 0:
    #         # credit entry
    #         move_lines.append((0, 0, {
    #             'name': "TESTE",
    #             'account_id': line.payment_order_id.payment_mode_id.writeoff_account_id.id,
    #             'partner_id': line.partner_id.id,
    #             'debit': 0,
    #             'credit': abs(write_off_amount),
    #             'company_id': journal and journal.company_id.id,
    #             'statement_id': statement_id,
    #         }))
    #     return move_lines

    # @api.model
    # def action_move_create(self, line, journal, amount_paid, statement_id):
    #     ctx = dict(self._context)
    #     account_move = self.env['account.move']
    #
    #     move_lines = self.move_lines_get(line, journal, amount_paid, statement_id)
    #     move_vals = {
    #         'ref': line.name,
    #         'line_ids': move_lines,
    #         'journal_id': journal and journal.id,
    #         'date': date.today(),
    #         # 'narration': inv.comment,
    #     }
    #     ctx['company_id'] = journal and journal.company_id.id
    #     ctx_nolang = ctx.copy()
    #     ctx_nolang.pop('lang', None)
    #     move = account_move.with_context(ctx_nolang).create(move_vals)
    #     move.post()
    #     return move

    @api.model
    def default_get(self, fields):
        res = super(AccountBankStatementImport, self).default_get(fields)
        file_format = self.env.context.get("file_format") or 'ofx'
        res['file_format'] = file_format
        res['force_format'] = True
        if file_format == 'cnab240':
            journal_id = self.env.context.get("active_id")
            # change journal id for cnab240
            journal_id = self.env['account.journal'].browse(journal_id).cnab_journal_id.id or journal_id
            res['journal_id'] = journal_id
            res['force_journal_account'] = True
        return res

    def get_explicit_error_message(self, message_dict, code, error):
        message = error_message = ''
        if code in message_dict.keys():
            message = message_dict.get(code)
        errors = [error[0:2], error[2:4], error[4:6], error[6:8]]
        for error in errors:
            error = int(error)
            # Table 1
            if code == 3 and table_1.get(error):
                error_message += str(error) + ' - ' + table_1.get(error) + '\n'
            # Table 2
            if code == 17 and table_2.get(error):
                error_message += str(error) + ' - ' + table_2.get(error) + '\n'
            # Table 3
            if code == 16 and table_3.get(error):
                error_message += str(error) + ' - ' + table_3.get(error) + '\n'
            # Table 4
            if code == 15 and table_4.get(error):
                error_message += str(error) + ' - ' + table_4.get(error) + '\n'
            # Table 5
            if code == 18 and table_5.get(error):
                error_message += str(error) + ' - ' + table_5.get(error) + '\n'
        return message, error_message

    @api.model
    def _create_bank_statements(self, stmt_vals):
        order_line_obj = self.env['payment.order.line']
        statement_line_line_obj = self.env['account.bank.statement.line']
        cnab_line_obj = self.env['cnab.lines']
        transactions = stmt_vals[0]['transactions'][:]
        bank_code = stmt_vals[0].get('bank_code', False)
        # remove bank_code
        stmt_vals[0].pop('bank_code', None)
        # omit trnasactions with servico_codigo_movimento != 6 for itau_cobranca_240
        # update jouranl_id for cnab240
        if len(stmt_vals):
            stmt_vals[0]['statement_type'] = self.file_format
        if self.file_format == 'cnab240':
            stmt_vals[0]['journal_id'] = self.journal_id.id
            # convert amount to float, base module does addition with float values
            index = 0
            index_list = []
            for transaction in stmt_vals[0]['transactions']:
                transaction.update({'amount': float(transaction.get('amount', 0.0))})
                if transaction.get('servico_codigo_movimento') not in [6, 8]:
                    index_list.append(index)
                index += 1
            [stmt_vals[0]['transactions'].pop(index) for index in index_list[::-1]]
        # call super only if there are transactions
        statement_id = False
        notifications = []
        if len(stmt_vals[0]['transactions']):
            statement_id, notifications = super(
                AccountBankStatementImport, self)._create_bank_statements(stmt_vals)
        if self.file_format == 'cnab240' and bank_code == '341':
            for line in transactions:
                # get service codigo message
                # first two chars in ref are from the year it was exported
                reference = line.get('ref')
                servico_codigo_movimento = line.get('servico_codigo_movimento')
                if reference:
                    order_line = order_line_obj.search(
                        [('nosso_numero', '=', reference), ('state', 'in', ['a', 'ag', 'e'])])
                    _logger.info(u'Matching to reconcile entry with nosso numero %s and service codigo %s' % (
                        reference, servico_codigo_movimento))
                    if len(order_line) > 1:
                        raise Warning(u"Multipe payment order lines found for reference %s" % reference)
                    if order_line:

                        error = str(line.get('errors'))
                        # remove unwnanted keys from dict
                        line.pop('errors', None)
                        line.pop('label', None)
                        line.pop('sequence', None)
                        line.pop('statement_id', None)
                        line.pop('bank_account_id,', None)
                        # Pago
                        if servico_codigo_movimento == 6 or servico_codigo_movimento == 8:
                            order_line.state = 'p'
                        # Aceito
                        if servico_codigo_movimento == 2:
                            order_line.state = 'a'
                        # Rejeitado
                        if servico_codigo_movimento == 3:
                            order_line.state = 'rj'
                        # Baixado
                        if servico_codigo_movimento == 5 or servico_codigo_movimento == 9 or servico_codigo_movimento == 32:
                            order_line.state = 'b'

                        message, error_message = self.get_explicit_error_message(service_codigo_message,
                                                                                 servico_codigo_movimento, error)

                        if message:
                            line.update({'servico_codigo_movimento':
                                             str(line['servico_codigo_movimento']) + ' - ' + message,
                                         'error_message': error_message,
                                         'cnab_line_id': order_line.id,
                                         })
                            cnab_line_obj.create(line)
        return statement_id, notifications


class AccountBankStatement(models.Model):
    """  """
    _inherit = 'account.bank.statement'

    statement_type = fields.Selection([('cnab240', 'cnab240'), ('ofx', 'ofx')], "Statement Type")

    # account.bank.statement.create() includes unknown fields:
    # account_number, bank, bank_code, currency_code
    # @api.model
    # def create(self, vals):
    #     vals.pop("bank", None)
    #     vals.pop("account_number", None)
    #     vals.pop("bank_code", None)
    #     vals.pop("currency_code", None)
    #     return super(AccountBankStatement, self).create(vals)


class AccountBankStatementLine(models.Model):
    """  """
    _inherit = 'account.bank.statement.line'

    servico_codigo_movimento = fields.Integer('Service Codigo Movimento',
                                              help='used this field to reconcile line after creation')

    @api.model
    def create(self, vals):
        order_line_obj = self.env['payment.order.line']
        res = super(AccountBankStatementLine, self).create(vals)
        if vals.get('servico_codigo_movimento') in [6, 8]:
            order_line = order_line_obj.search([('nosso_numero', '=', res.ref), ('state', 'in', ['a', 'e'])])
            if len(order_line) > 1:
                raise Warning(u"Multipe payment order lines found for reference %s" % res.ref)
            # reconcile bank statement line
            if order_line and order_line.move_line_id:
                aml = order_line.move_line_id
                amount = res.amount  # statement line amount (received value in bank)
                value = order_line.value  # payment order line value ( expected value to be received)
                data_dict = {'payment_aml_ids': []}
                # counter part move line
                data_dict.update({'counterpart_aml_dicts': [{'credit': value > 0 and value or 0,
                                                             'counterpart_aml_id': aml.id,
                                                             'name': aml.name if aml.name != '/' else aml.move_id.name,
                                                             'debit': value < 0 and value or 0}
                                                            ]})
                # write-off if exists
                writeoff_amount = amount - value
                if writeoff_amount != 0:
                    if not order_line.payment_order_id.payment_mode_id.writeoff_account_id:
                        raise Warning(u"Writeoff acount not set in payment mode in %s" % (
                            order_line.payment_order_id.payment_mode_id and order_line.payment_order_id.payment_mode_id.name))
                    account = order_line.payment_order_id.payment_mode_id.writeoff_account_id
                    data_dict.update({'new_aml_dicts': [{'credit': writeoff_amount > 0 and abs(writeoff_amount) or 0,
                                                         'debit': writeoff_amount < 0 and abs(writeoff_amount) or 0,
                                                         'account_id': account.id,
                                                         'name': account.name}]})
                data = []
                data.append(data_dict)
                res.process_reconciliations(data)
        return res
