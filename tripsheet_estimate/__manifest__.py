# -*- coding: utf-8 -*-
{
    'name': 'Estimate Trip Sheet',
    'version': '14.0',
    'summary': 'Estimate',
    'author':
        'ENZAPPS',
    'sequence': 20,
    'description': """Brother Inv Rounding Custom""",
    'category': '',
    'website': 'https://enzapps.com',
    'depends': ['base', 'contacts','account','ezp_estimate','enz_multi_updations','enz_mc_owner','ezp_cash_collection','brothers_trip_sheet_30','enz_mc_owner'],
    'images': ['static/description/logo.png'],
    'data': [
        'views/account_move.xml'
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,

}
