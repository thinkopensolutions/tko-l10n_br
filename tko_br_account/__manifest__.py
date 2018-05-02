# -*- coding: utf-8 -*-
# © 2017 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'TKO Account Brasileiro',
    'summary': '',
    'description': 'Set Tipo de Serviço non required',
    'author': 'TKO',
    'category': 'l10n_br',
    'license': 'AGPL-3',
    'website': 'http://tko.tko-br.com',
    'version': '10.0.0.0.0',
    'application': False,
    'installable': True,
    'auto_install': False,
    'depends': [
        'br_account_payment',
        'br_account',
        'br_boleto',
        'br_account_einvoice',
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'data/payment_sequence_view.xml',
        'views/account_bank_statement_view.xml',
        'views/account_invoice_view.xml',
        'views/account_tax_view.xml',
        'views/account_view.xml',
        'views/product_view.xml', ],
    'css': [],
    'demo_xml': [],
    'test': [],
    'data': [
        'views/account_view.xml',
    ],

}
