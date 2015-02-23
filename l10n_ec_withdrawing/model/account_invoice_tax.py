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
from openerp import api, models, fields
import time
class AccountInvoiceTax(models.Model):

    _name = 'account.invoice.tax'
    _inherit = 'account.invoice.tax'

    fiscal_year = fields.Char(size = 4, default=time.strftime('%Y'))
    tax_group = fields.Selection([('vat','IVA Diferente de 0%'),
                                        ('vat0','IVA 0%'),
                                        ('novat','No objeto de IVA'),
                                        ('ret_vat_b', 'Retención de IVA(Bienes)'),
                                        ('ret_vat_srv', 'Retención de IVA(Servicios)'),
                                        ('ret_ir', 'Ret. Imp. Renta'),
                                        ('no_ret_ir', 'No sujetos a Ret. de Imp. Renta'),
                                        ('imp_ad', 'Imps. Aduanas'),
                                        ('ice', 'ICE'),
                                        ('other','Other')], required=True)
    percent = fields.Char(size=20)
    num_document = fields.Char(size=50)
    retention_id = fields.Many2one('account.retention')

    @api.v8
    def compute(self, active_invoice):
        tax_grouped = {}
        cur = self.env['res.currency'].browse( active_invoice.company_id.id)
        for line in active_invoice.invoice_line:
            _quantity = line.quantity
            _discount = line.discount
            _price = line.price_unit * (1-(_discount or 0.0)/100.0)

            for tax in  line.invoice_line_tax_id.compute_all(_price, _quantity,
                    product = line.product_id,
                    partner = line.invoice_id.partner_id)['taxes']:
                val={}
                val['tax_group'] = tax['tax_group']
                val['percent'] = tax['porcentaje']
                val['invoice_id'] = line.invoice_id.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = cur.round( tax['price_unit'] * line['quantity'])
                # Hack to EC
                if tax['tax_group'] in ['ret_vat_b', 'ret_vat_srv']:
                    ret = float(str(tax['porcentaje'])) / 100
                    bi = tax['price_unit'] * line['quantity']
                    imp = (abs(tax['amount']) / (ret * bi)) * 100
                    val['base'] = (tax['price_unit'] * line['quantity']) * imp / 100
                else:
                    val['base'] = tax['price_unit'] * line['quantity']

                if line.invoice_id.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur.compute(
                            val['base'] * tax['base_sign'],
                            line.invoice_id.currency_id,
                            round = False
                            )
                    val['tax_amount'] =cur.compute(\
                        val['amount'] * tax['tax_sign'],
                        line.invoice_id.currency_id,
                        round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] =cur.compute(\
                        val['base'] * tax['ref_base_sign'],
                        line.invoice_id.currency_id,
                        round=False)
                    val['tax_amount'] =cur.compute(\
                        val['amount'] * tax['ref_tax_sign'],
                        line.invoice_id.currency_id,
                        round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']

                # If the taxes generate moves on the same financial account as the invoice line
                # and no default analytic account is defined at the tax level, propagate the
                # analytic account from the invoice line to the tax line. This is necessary
                # in situations were (part of) the taxes cannot be reclaimed,
                # to ensure the tax move is allocated to the proper analytic account.
                if not val.get('account_analytic_id') and line.account_analytic_id and val['account_id'] == line.account_id.id:
                    val['account_analytic_id'] = line.account_analytic_id.id

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = cur.round(t['base'])
            t['amount'] = cur.round(t['amount'])
            t['base_amount'] = cur.round(t['base_amount'])
            t['tax_amount'] = cur.round(t['tax_amount'])
        return tax_grouped

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
