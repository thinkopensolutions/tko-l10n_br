# -*- coding: utf-8 -*-
# © 2017 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'TKO Account Cost Center',
    'summary': '',
    'description': 'Add cost center in invoice lines (l10_br)',
    'author': 'TKO',
    'category': 'l10n_br',
    'license': 'AGPL-3',
    'website': 'http://tko.tko-br.com',
    'version': '10.0.0.0.0',
    'application': False,
    'installable': True,
    'auto_install': True,
    'depends': [
        'br_account',
        'account_cost_center',
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'init_xml': [],
    'update_xml': [
       ],
    'css': [],
    'demo_xml': [],
    'test': [],
    'data': [
        'views/account_invoice_view.xml',
    ],

}
