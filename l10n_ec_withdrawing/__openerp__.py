# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Module - Ecuador
#    Copyright (C) 2009 GnuThink Software All Rights Reserved
#    info@gnuthink.com
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name' : 'Withdrawing for Ecuador',
    'version' : '7.0',
    "category": 'Accounting/Ecuador',
    'depends' : ['l10n_ec_authorisation', 'report_webkit',
        ],
    'author' : 'Cristian Salamea.',
    'description': '''
    Accounting for Ecuador, retention docuements
    ''',
    'website': 'http://www.ayni.io',
    'update_xml': [
    ],
    'data':[
        'withdrawing_report.xml',
        'withdrawing_view.xml',
        'invoice_workflow.xml',
        'retention_wizard.xml',
        'data/account.fiscal.position.csv'

        ],
    'installable': True,
    'active': False,
}
