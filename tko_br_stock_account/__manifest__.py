# -*- coding: utf-8 -*-
# © 2017 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'TKO Stock Account Brasileiro',
    'summary': '',
    'description': 'compute invoice with frete, seguro, despesas and account moves with them',
    'author': 'TKO',
    'category': 'l10n_br',
    'license': 'AGPL-3',
    'website': 'http://tko.tko-br.com',
    'version': '10.0.0.0.0',
    'application': False,
    'installable': True,
    'auto_install': True,
    'depends': [
        'tko_br_account',
        'br_stock_account',
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'init_xml': [],
    'data': [],
    'css': [],
    'demo_xml': [],
    'test': [],

}
