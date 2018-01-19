# -*-coding:utf-8-*-
from odoo import models, fields, api, _
from calendar import monthrange
import datetime
import decimal
import tempfile
import StringIO
import logging
_logger = logging.getLogger(__name__)
try:
    from cnab240.bancos import sicoob
    from cnab240.tipos import Arquivo
    from ofxparse import OfxParser
except ImportError:
    _logger.debug('Cannot import cnab240 or ofxparse dependencies.')


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    @api.multi
    def import_file(self):
        res = super(AccountBankStatementImport, self).import_file()
        if self.file_format == 'ofx':
            return True
        return True

    def _parse_ofx(self, data_file):
        data_file = data_file.replace('\r\n', '\n').replace('\r', '\n')
        ofx = OfxParser.parse(StringIO.StringIO(data_file))
        transacoes = []
        total = 0.0
        #index = 1  # Some banks don't use a unique transaction id, we make one
        for account in ofx.accounts:
            for transacao in account.statement.transactions:
                transacoes.append({
                    'date': transacao.date,
                    'name': transacao.payee + (
                        transacao.memo and ': ' + transacao.memo or ''),
                    'ref': transacao.id,
                    'amount': transacao.amount,
                    'unique_import_id': "%s" % (transacao.id,)
                })
                total += float(transacao.amount)
                #index += 1
        # Really? Still using Brazilian Cruzeiros :/
        if ofx.account.statement.currency.upper() == "BRC":
            ofx.account.statement.currency = "BRL"

        journal = self.journal_id
        if not self.force_journal_account:
            dummy, journal = self._find_additional_data(
                ofx.account.statement.currency, ofx.account.number)

        month =  ofx.account.statement.start_date.month
        year = ofx.account.statement.start_date.year
        name = u"%s -%s" % (
            journal.name,'replace_date'
        )
        vals_bank_statement = {
            'name': name,
            'transactions': transacoes,
            'balance_start': 0.0,
            'balance_end_real': 0.0,
        }
        account_number = ofx.account.number
        if self.force_journal_account:
            account_number = self.journal_id.bank_account_id.sanitized_acc_number
        return (
            ofx.account.statement.currency,
            account_number,
            [vals_bank_statement]
        )

    def _create_bank_statements(self, stmts_vals):
        def update_bank_statement_ending_balance(bank_statement, amount):
            bank_statement.write({'balance_end_real': decimal.Decimal(bank_statement.balance_end_real) + amount})
            return True

        if self.file_format != 'ofx':
            return super(AccountBankStatementImport, self)._create_bank_statements(stmts_vals)
        BankStatement = self.env['account.bank.statement']
        BankStatementLine = self.env['account.bank.statement.line']
        AcccountJournal = self.env['account.journal']
        statement_ids = []
        ignored_statement_lines_import_ids = []
        stmt_vals = stmts_vals[0].copy()
        stmt_vals.pop('transactions', None)

        if len(stmts_vals):
            for st_vals in stmts_vals[0].get('transactions'):
                date = st_vals['date']
                # set date and clear followers raising issue can't follow same doc twice
                stmt_vals['date'] = st_vals['date']
                stmt_vals['message_follower_ids'] = False
                last_day = monthrange(date.year, date.month)[1]
                # search statement between start and end date
                start = datetime.date(year=date.year, month=date.month, day=1)
                end = datetime.date(year=date.year, month=date.month, day=last_day)
                journal_id = self.env.context.get('active_id', False)
                journal = self.env['account.journal'].browse(journal_id)
                bank_statement = BankStatement.search(
                    [('date', '>=', start), ('date', '<=', end), ('state', '=', 'open'),('journal_id','=',journal_id)], limit=1)
                # previous month

                pre_start = datetime.date(year=date.year, month=date.month - 1 if date.month > 1 else 12, day=1)
                last_day = monthrange(date.year, date.month -1 if date.month > 1 else 12)[1]
                pre_end = datetime.date(year=date.year, month=date.month - 1 if date.month > 1 else 12, day=last_day)

                pre_bank_statement = BankStatement.search(
                    [('date', '>=', pre_start), ('date', '<=', pre_end),('journal_id','=',journal_id)], limit=1)
                if len(pre_bank_statement):
                    stmt_vals['balance_start'] = pre_bank_statement.balance_end_real
                    stmt_vals['balance_end_real'] = pre_bank_statement.balance_end_real

                # create statement for the month if not found
                if not (bank_statement):
                    name = u"%s - %s/%s" % (journal.name, date.month, date.year)
                    stmt_vals['name'] = name
                    bank_statement = BankStatement.create(stmt_vals)
                st_vals['statement_id'] = bank_statement.id
                # create  statement line in found bank statement
                if not bool(BankStatementLine.sudo().search([('unique_import_id', '=', st_vals['unique_import_id'])],
                                                            limit=1)):
                    # create statement line if not exisitng
                    BankStatementLine.create(st_vals)
                    # update ending balance in statement
                    update_bank_statement_ending_balance(bank_statement, st_vals.get('amount', 0.0))

        return [], []
