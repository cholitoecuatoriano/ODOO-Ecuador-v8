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

# @author : 'marcelowmora', 'marcelo.mora@accioma.com'


from openerp.tests.common import TransactionCase
from openerp.tools import mute_logger
from datetime import datetime

class GlobalTestElectronicInvoice(TransactionCase):
    """
    Global Test Electronic Invoicing
    - Access key generation
    - Xml file generation
    """

    def setUp(self):
        super(GlobalTestElectronicInvoice, self).setUp()
        self.invoice = self.env['account.invoice']
        self.partner = self.env['res.partner']
        self.authorisation = self.env['account.authorisation']
        self.journal = self.env['account.journal']
        self.account = self.env['account.account']

    def create_invoice(self, partner, authorisation, journal, account, date_invoice):
        return self.invoice.create({
           'supplier_invoice_number' : '001-001-000000234',
           'partner_id' : partner.id,
           'auth_inv_id' : authorisation.id,
           'date_invoice' : date_invoice,
           'journal_id' : journal.id,
           'account_id' : account.id,
           })

    def test_10_access_key_generation(self):
        print "========================================="
        print "====== Testing Key Generation ==========="
        print "========================================="
        print "Create invoice"
        partner = self.partner.env.ref("l10n_ec_partner.einvoice_partner_02")
        auth = self.authorisation.env.ref("l10n_ec_authorisation.invoice_auth_customer")
        journal = self.journal.env.ref("l10n_ec_authorisation.diario_ventas")
        account = self.account.env.ref("__export__.account_account_42")

        print journal._name

        inv = self.create_invoice(partner, auth, journal, account, datetime.now().strftime("%Y-%m-%d"))
        print inv._compute_access_key()

"""
        # Check if date, sequence and ruc are placed correctly
"""


