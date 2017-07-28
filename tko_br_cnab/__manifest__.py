# -*- coding: utf-8 -*-
# © 2017 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'CNAB240',
    'summary': '',
    'description': 'CNAB240.',
    'author': 'TKO',
    'category': 'l10n_br',
    'license': 'AGPL-3',
    'website': 'http://tko.tko-br.com',
    'version': '10.0.0.0.0',
    'application': False,
    'installable': True,
    'auto_install': False,
    'depends': [
        'br_cnab',
        'br_boleto',
        'br_bank_statement_import',
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'init_xml': [],
    'update_xml': [],
    'css': [],
    'demo_xml': [],
    'test': [],
    'data': [
        'wizard/import_order_lines_view.xml',
        'wizard/mail_sent_info_view.xml',
        'views/payment_order_view.xml',
        'views/journal_view.xml',
        'views/account_bank_statement_import_view.xml',

    ],

}
