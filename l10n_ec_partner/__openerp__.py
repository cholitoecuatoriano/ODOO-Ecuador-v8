# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Cristian Salamea.
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
    'name' : 'OpenERP Partner for Ecuador',
    'version' : '0.1.1',
    'author' : 'Cristian Salamea, Marcelo Mora',
    'category': 'Ecuadorian Localization',
    'complexity': 'normal',
    'website': 'http://accioma.com',
    'data': [
        'view/partner_view.xml',
    ],
    'depends' : [
      'base'
    ],
    'js': [
    ],
    'qweb': [
    ],
    'css': [
    ],
    'test': [
    ],
    'demo' : [
        'demo/partner_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
