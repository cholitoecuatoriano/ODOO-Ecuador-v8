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
from .xades import xades

tipoDocumento = { #tabla 4 en la ficha tecnica
    '01': '01',
    '04': '04',
    '05': '05',
    '06': '06',
    '07': '07',
    '18': '01',
}

tipoIdentificacion = {
    'ruc' : '04',
    'cedula' : '05',
    'pasaporte' : '06',
    'venta_consumidor_final' : '07',
    'identificacion_exterior' : '08',
    'placa' : '09',
}

codigoImpuesto = {
    'vat': '2',
    'vat0': '2',
    'ice': '3',
    'other': '5'
}

tarifaImpuesto = {
    'vat0': '0',
    'vat': '2',
    'novat': '6',
    'other': '7',
}

invtypes_04 = {
        'out_invoice' : '01',
}

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _check_service_availability(self):
        return True

    @api.one
    @api.depends('date_invoice','journal_id','company_id','estab','ptoEmi','secuencial')
    def _compute_access_key(self):
        codigo_numero = '12345678'
        #tipo_emision = self.company_id.emission_code
        tipo_emision = '1' #1 normal, 2 indisponibilidad

        access_number = "{}{}{}{}{}{}{}{}".format(
                "".join(reversed(self.date_invoice.split('-'))),
                tipoDocumento[self.journal_id.auth_id.type_id.code],
                self.company_id.partner_id.ced_ruc,
                "1",
                "{}{}".format(self.estab, self.ptoEmi),
                "{0:09d}".format(self.secuencial),
                codigo_numero,
                tipo_emision)

        check_digit = xades.CheckDigit().compute_mod11(access_number)
        self.access_key = "{}{}".format(access_number, check_digit)

        print self.access_key

    access_key = fields.Char(string = 'Access Key',
            compute="_compute_access_key",
            help='Access Key for document', readonly=True)
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




