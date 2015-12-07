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

from openerp import api, exceptions, fields, models
import openerp.addons.decimal_precision as dp
import datetime
from lxml import etree

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    def _compute_access_key(self):
        auth = self.journal_id.auth_id
        ld = self.date_invoice.split('-')
        ld.reverse()
        fecha = ''.join(ld)
        #tcomp = tipoDocumento[auth.type_id.code]
        tcomp = '01'
        ruc = self.company_id.partner_id.ced_ruc
        serie = '{0}{1}'.format(auth.serie_entidad, auth.serie_emision)
        numero = self.number[6:15]
        #TODO: security code
        codigo_numero = '12345678'
        tipo_emision = self.company_id.emission_code
        access_key = (
            [fecha, tcomp, ruc],
            [serie, numero, codigo_numero, tipo_emision]
            )
        return access_key


    access_key = fields.Char(string = 'Access Key'
                             , help='Access Key for document', readonly=True)
    auth_number = fields.Char(string = 'Authorization Number',
            readonly = True, help = "Authorization Number")
    auth_status = fields.Char(string = "Authorization status", readonly=True,
            help = "Status of Authorization depends on SRI")
    einv_env = fields.Selection(string = "Environment",
            selection = [('01', 'Tests'),('02','Production')],
            help="Environment used to issue electronic voucher")
    is_sri_approved = fields.Boolean(sting = "SRI Approved?", readonly=True,
            help = "Is Approved by SRI?")
    securiry_code = fields.Char(string="Security Code", readonly=True,
            help = "Security code")
    issuing_type = fields.Selection(string = "Issuing Type",
            selection = [('1', "Issuing normal"),
                         ('2', "Issuing at no available system")],
            help = "Issuing type. Table 2")

    def _get_tax_element(self, invoice, access_key, emission_code):
        """
        """
        company = invoice.company_id
        auth = invoice.journal_id.auth_id
        infoTributaria = etree.Element('infoTributaria')
        etree.SubElement(infoTributaria, 'ambiente').text = SriService.get_active_env()
        etree.SubElement(infoTributaria, 'tipoEmision').text = emission_code
        etree.SubElement(infoTributaria, 'razonSocial').text = company.name
        etree.SubElement(infoTributaria, 'nombreComercial').text = company.name
        etree.SubElement(infoTributaria, 'ruc').text = company.partner_id.ced_ruc
        etree.SubElement(infoTributaria, 'claveAcceso').text = access_key
        etree.SubElement(infoTributaria, 'codDoc').text = tipoDocumento[auth.type_id.code]
        etree.SubElement(infoTributaria, 'estab').text = auth.serie_entidad
        etree.SubElement(infoTributaria, 'ptoEmi').text = auth.serie_emision
        etree.SubElement(infoTributaria, 'secuencial').text = invoice.number[6:15]
        etree.SubElement(infoTributaria, 'dirMatriz').text = company.street
        return infoTributaria




