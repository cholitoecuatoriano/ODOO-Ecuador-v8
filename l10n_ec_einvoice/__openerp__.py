# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name' : 'Ecuadorian Electronic Invoicing',
    'version' : '0.1',
    'author' : 'Accioma',
    'category' : 'EC Localization',
    'description' : """
Electronic Invoicing
=============================
Ecuadorian Localization
-----------------------------
Support for electronic invoicing:
- Send commercial vouchers to SRI webservices
- Manage for authorized and not authorized vouchers
- Automatic processing for incoming vouchers
- Website optimization for display of information of electronic vouchers

    """,
    'website': 'http://www.accioma.com',
    'images' : [],
    'depends' : [
        'base', 'l10n_ec_invoice_sequence', 'l10n_ec_withdrawing',
    ],
    'data': [
        'view/account_invoice_view.xml',
    ],
    'js': [
    ],
    'qweb' : [
    ],
    'css':[
    ],
    'demo': [
    ],
    'test': [
#        'test/account_customer_invoice.yml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

