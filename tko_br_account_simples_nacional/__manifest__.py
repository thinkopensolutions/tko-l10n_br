# -*- coding: utf-8 -*-
# © 2017 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Imposto Simples Nacional',
    'summary': '',
    'description': 'Calcula faturamento nos últimos 12 meses e habilita cálculo especial do imposto tipo Simples Nacional.',
    'author': 'TKO',
    'category': 'l10n_br',
    'license': 'AGPL-3',
    'website': 'http://tko.tko-br.com',
    'version': '10.0.0.0.0',
    'application': False,
    'installable': True,
    'auto_install': False,
    'depends': ['br_account',
                'br_account_einvoice'],
    'external_dependencies': {
                                'python': [],
                                'bin': [],
                                },
    'init_xml': [],
    'update_xml': [
        'views/simples_nacional_view.xml',
        'views/res_company_view.xml',
        'views/account_invoice_view.xml',
    ],
    'css': [],
    'demo_xml': [],
    'test': [],
    'data': [],

}
