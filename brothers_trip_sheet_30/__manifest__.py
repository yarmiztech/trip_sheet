# -*- coding: utf-8 -*-
{
    'name': 'Brothers Trip Sheet',
    'version': '1.0',
    'summary': 'Brothers Trip Sheet',
    'sequence': -100,
    'description': """Brothers Trip Sheet""",
    'category': '',
    'website': 'https://enzapps.com',
    'license': 'LGPL-3',
    'depends': ['base', 'contacts', 'account','fleet'],
    'images': ['static/description/logo.png'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/configuration.xml',
        'views/batta_configuration.xml',
        'views/trip_sheet.xml',
        'views/trip_sheet_report.xml',
        'views/basic_configuration.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,

}
