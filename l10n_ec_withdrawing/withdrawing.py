# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Module - Ecuador
#    Copyright (C) 2014 Cristian Salamea All Rights Reserved
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

import time
import logging
from openerp.osv import osv, fields
from openerp.tools import config
from openerp.tools.translate import _
from openerp.tools import ustr
import openerp.addons.decimal_precision as dp
import openerp.netsvc
#import pdb

from openerp import models, api

class AccountWithdrawing(osv.osv):

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        res = []
        reads = self.browse(cr, uid, ids, context=context)
        for record in reads:
            name = record.name
            res.append((record.id, name))
        return res

    def _amount_total(self, cr, uid, ids, field_name, args, context):
        res = {}
        retentions = self.browse(cr, uid, ids, context)
        for ret in retentions:
            total = 0
            for tax in ret.tax_ids:
                total += tax.amount
            res[ret.id] = abs(total)
        return res

    def _get_period(self, cr, uid, ids, fields, args, context):
        res = {}
        period_obj = self.pool.get('account.period')
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id] = period_obj.find(cr, uid, obj.date)[0]
        return res

    STATES_VALUE = {'draft': [('readonly', False)]}

    _name = 'account.retention'
    _description = 'Withdrawing Documents'
    _order = 'date desc, name desc'

    _columns = {
        'name': fields.char('Number', size=64, readonly=True,
                            required=True,
                            states=STATES_VALUE),
        'manual': fields.boolean('Manual sequence number', readonly=True,
                                 states=STATES_VALUE),
        'num_document': fields.char('Voucher number', size=50,
                                    readonly=True,
                                    states=STATES_VALUE),
        'auth_id': fields.many2one(
            'account.authorisation',
            'Autorizacion',
            readonly=True,
            states=STATES_VALUE,
            required=True,
            domain=[('in_type','=','interno')]
            ),
        'type': fields.selection(
            [('in_invoice','Factura'),
            ('liq_purchase','Liquidacion Compra')],
            string='Tipo Comprobante',
            readonly=True, states=STATES_VALUE
            ),
        'in_type': fields.selection(
            [('ret_in_invoice', u'Retención a Proveedor'),
            ('ret_out_invoice', u'Retención de Cliente')],
            string='Tipo',
            states=STATES_VALUE,
            readonly=True),
        'date': fields.date('Fecha Emision', readonly=True,
                            states={'draft': [('readonly', False)]}, required=True),
        'period_id': fields.many2one(
            'account.period',
            'Periodo',
            required=True
            ),
        'tax_ids': fields.one2many(
            'account.invoice.tax',
            'retention_id',
            'Detalle de Impuestos',
            readonly=True,
            states=STATES_VALUE
            ),
        'invoice_id': fields.many2one(
            'account.invoice',
            string='Documento',
            required=False,
            readonly=True,
            states=STATES_VALUE,
            domain=[('state','=','open')]
            ),
        'partner_id': fields.related(
            'invoice_id',
            'partner_id',
            type='many2one',
            relation='res.partner',
            string='Empresa',
            readonly=True
            ),
        'move_id': fields.related(
            'invoice_id',
            'move_id',
            type='many2one',
            relation='account.move',
            string='Asiento Contable',
            readonly=True
            ),
        'state': fields.selection(
            [('draft','Borrador'),
            ('early','Anticipado'),
            ('done','Validado'),
            ('cancel','Anulado')],
            readonly=True,
            string='Estado'
            ),
        'amount_total': fields.function(
            _amount_total, string='Total',
            method=True, store=True,
            digits_compute=dp.get_precision('Account')
            ),
        'to_cancel': fields.boolean('Para anulación',readonly=True, states=STATES_VALUE),
        'company_id': fields.many2one(
            'res.company',
            'Company',
            required=True,
            change_default=True,
            readonly=True,
            states={'draft':[('readonly',False)]}
            ),
        }

    def _get_period(self, cr, uid, context=None):
        res = self.pool.get('account.period').find(cr, uid, context=context)
        return res and res[0] or False

    def _get_type(self, cr, uid, context):
        if context.has_key('type') and \
        context['type'] in ['in_invoice', 'out_invoice']:
            return 'in_invoice'
        else:
            return 'liq_purchase'

    def _get_in_type(self, cr, uid, context):
        if context.has_key('type') and \
        context['type'] in ['in_invoice', 'liq_purchase']:
            return 'ret_in_invoice'
        else:
            return 'ret_in_invoice'

    _defaults = {
        'state': 'draft',
        'in_type': _get_in_type,
        'type': _get_type,
        'name': '/',
        'manual': True,
        'date': time.strftime('%Y-%m-%d'),
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
        'period_id': _get_period
        }

    _sql_constraints = [('unique_number_name', 'unique(name)', u'El número de retención es único.')]

    def unlink(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context):
            if obj.state in ['done']:
                raise osv.except_osv('Aviso','No se permite borrar retenciones validadas.')
        res = super(AccountWithdrawing, self).unlink(cr, uid, ids, context)
        return res

    def onchange_invoice(self, cr, uid, ids, invoice_id):
        res = {'value': {'num_document': ''}}
        if not invoice_id:
            return res
        invoice = self.pool.get('account.invoice').browse(cr, uid, invoice_id)
        if not invoice.auth_inv_id:
            return res
        num_document = invoice.supplier_number
        print num_document
        res['value']['num_document'] = num_document
        res['value']['type'] = invoice.type
        return res

    def button_validate(self, cr, uid, ids, context=None):
        """
        Botón de validación de Retención que se usa cuando
        se creó una retención manual, esta se relacionará
        con la factura seleccionada.
        """
        invoice_obj = self.pool.get('account.invoice')
        if context is None:
            context = {}
        for ret in self.browse(cr, uid, ids, context):
            if ret.manual:
                self.action_validate(cr, uid, [ret.id], ret.name)
                invoice_obj.write(cr, uid, ret.invoice_id.id, {'retention_id': ret.id})
            else:
                self.action_validate(cr, uid, [ret.id])
        return True

    def action_validate(self, cr, uid, ids, number=None):
        '''
        cr: cursor de la base de datos
        uid: ID de usuario
        ids: lista ID del objeto instanciado
        number: Numero posible para usar en el documento

        Metodo que valida el documento, su principal
        accion es numerar el documento segun el parametro number
        '''
        seq_obj = self.pool.get('ir.sequence')
        for ret in self.browse(cr, uid, ids):
            if ret.to_cancel:
                raise osv.except_osv('Alerta', 'El documento fue marcado para anular.')
            seq_id = ret.invoice_id.journal_id.auth_ret_id.sequence_id.id
            seq = seq_obj.browse(cr, uid, seq_id)
            ret_num = number
            if number is None:
                ret_number = seq_obj.get(cr, uid, seq.code)
            else:
                padding = seq.padding
                ret_number = str(number).zfill(padding)
            self._amount_total(cr, uid, [ret.id], [], {}, {})
            number = ret.auth_id.serie_entidad + ret.auth_id.serie_emision + ret_number
            self.write(cr, uid, ret.id, {'state': 'done', 'name':number})
            self.log(cr, uid, ret.id, _("La retención %s fue generada.") % number)
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        '''
        cr: cursor de la base de datos
        uid: ID de usuario
        ids: lista ID del objeto instanciado

        Metodo para cambiar de estado a cancelado
        el documento
        '''
        auth_obj = self.pool.get('account.authorisation')
        for ret in self.browse(cr, uid, ids):
            data = {'state': 'cancel'}
            if ret.to_cancel:
                if len(ret.name) == 9 and auth_obj.is_valid_number(cr, uid, ret.auth_id.id, int(ret.name)):
                    number = ret.auth_id.serie_entidad + ret.auth_id.serie_emision + ret.name
                    data.update({'name': number})
                else:
                    raise osv.except_osv('Error', u'El número no es de 9 dígitos y/o no pertenece a la autorización seleccionada.')
            self.write(cr, uid, ret.id, data)
        return True

    def action_draft(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context):
            name = obj.name[6:]
            self.write(cr, uid, ids, {'state': 'draft', 'name': name}, context)
        return True

    def action_early(self, cr, uid, ids, *args):
        '''
        cr: cursor de la base de datos
        uid: ID de usuario
        ids: lista ID del objeto instanciado

        Metodo para cambiar de estado a cancelado
        el documento
        '''
        self.write(cr, uid, ids, {'state': 'early'})
        return True




class Invoice(osv.osv):

    _inherit = 'account.invoice'
    __logger = logging.getLogger(_inherit)

    def onchange_company_id(self, cr, uid, ids, company_id, part_id, type, invoice_line, currency_id):
        #TODO: add the missing context parameter when forward-porting in trunk so we can remove
        #      this hack!
        context = self.pool['res.users'].context_get(cr, uid)

        val = {}
        dom = {}
        obj_journal = self.pool.get('account.journal')
        account_obj = self.pool.get('account.account')
        inv_line_obj = self.pool.get('account.invoice.line')
        if company_id and part_id and type:
            acc_id = False
            partner_obj = self.pool.get('res.partner').browse(cr,uid,part_id)
            if partner_obj.property_account_payable and partner_obj.property_account_receivable:
                if partner_obj.property_account_payable.company_id.id != company_id and partner_obj.property_account_receivable.company_id.id != company_id:
                    property_obj = self.pool.get('ir.property')
                    rec_pro_id = property_obj.search(cr, uid, [('name','=','property_account_receivable'),('res_id','=','res.partner,'+str(part_id)+''),('company_id','=',company_id)])
                    pay_pro_id = property_obj.search(cr, uid, [('name','=','property_account_payable'),('res_id','=','res.partner,'+str(part_id)+''),('company_id','=',company_id)])
                    if not rec_pro_id:
                        rec_pro_id = property_obj.search(cr, uid, [('name','=','property_account_receivable'),('company_id','=',company_id)])
                    if not pay_pro_id:
                        pay_pro_id = property_obj.search(cr, uid, [('name','=','property_account_payable'),('company_id','=',company_id)])
                    rec_line_data = property_obj.read(cr, uid, rec_pro_id, ['name','value_reference','res_id'])
                    pay_line_data = property_obj.read(cr, uid, pay_pro_id, ['name','value_reference','res_id'])
                    rec_res_id = rec_line_data and rec_line_data[0].get('value_reference',False) and int(rec_line_data[0]['value_reference'].split(',')[1]) or False
                    pay_res_id = pay_line_data and pay_line_data[0].get('value_reference',False) and int(pay_line_data[0]['value_reference'].split(',')[1]) or False
                    if not rec_res_id and not pay_res_id:
                        raise osv.except_osv(_('Configuration Error!'),
                            _('Cannot find a chart of account, you should create one from Settings\Configuration\Accounting menu.'))
                    if type in ('out_invoice', 'out_refund'):
                        acc_id = rec_res_id
                    else:
                        acc_id = pay_res_id
                    val= {'account_id': acc_id}
            if ids:
                if company_id:
                    inv_obj = self.browse(cr,uid,ids)
                    for line in inv_obj[0].invoice_line:
                        if line.account_id:
                            if line.account_id.company_id.id != company_id:
                                result_id = account_obj.search(cr, uid, [('name','=',line.account_id.name),('company_id','=',company_id)])
                                if not result_id:
                                    raise osv.except_osv(_('Configuration Error!'),
                                        _('Cannot find a chart of account, you should create one from Settings\Configuration\Accounting menu.'))
                                inv_line_obj.write(cr, uid, [line.id], {'account_id': result_id[-1]})
            else:
                if invoice_line:
                    for inv_line in invoice_line:
                        obj_l = account_obj.browse(cr, uid, inv_line[2]['account_id'])
                        if obj_l.company_id.id != company_id:
                            raise osv.except_osv(_('Configuration Error!'),
                                _('Invoice line account\'s company and invoice\'s company does not match.'))
                        else:
                            continue
        if company_id and type:
            journal_mapping = {
               'out_invoice': 'sale',
               'out_refund': 'sale_refund',
               'in_refund': 'purchase_refund',
               'in_invoice': 'purchase',
               'liq_purchase': 'purchase'
            }
            journal_type = journal_mapping[type]
            journal_ids = obj_journal.search(cr, uid, [('company_id','=',company_id), ('type', '=', journal_type)])
            if journal_ids:
                val['journal_id'] = journal_ids[0]
            ir_values_obj = self.pool.get('ir.values')
            res_journal_default = ir_values_obj.get(cr, uid, 'default', 'type=%s' % (type), ['account.invoice'])
            for r in res_journal_default:
                if r[1] == 'journal_id' and r[2] in journal_ids:
                    val['journal_id'] = r[2]
            if not val.get('journal_id', False):
                journal_type_map = dict(obj_journal._columns['type'].selection)
                journal_type_label = self.pool['ir.translation']._get_source(cr, uid, None, ('code','selection'),
                                                                             context.get('lang'),
                                                                             journal_type_map.get(journal_type))
                raise osv.except_osv(_('Configuration Error!'),
                                     _('Cannot find any account journal of %s type for this company.\n\nYou can create one in the menu: \nConfiguration\Journals\Journals.') % ('"%s"' % journal_type_label))
            dom = {'journal_id':  [('id', 'in', journal_ids)]}
        else:
            journal_ids = obj_journal.search(cr, uid, [])

        return {'value': val, 'domain': dom}

    def onchange_sustento(self, cr, uid, ids, sustento_id):
        res = {'value': {}}
        if not sustento_id:
            return res
        sustento = self.pool.get('account.ats.sustento').browse(cr, uid, sustento_id)
        res['value']['name'] = sustento.type
        return res

    def print_invoice(self, cr, uid, ids, context=None):
        '''
        cr: cursor de la base de datos
        uid: ID de usuario
        ids: lista ID del objeto instanciado

        Metodo para imprimir reporte de liquidacion de compra
        '''
        if not context:
            context = {}
        invoice = self.browse(cr, uid, ids, context)[0]
        datas = {'ids': [invoice.id], 'model': 'account.invoice'}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'invoice_report',
            'model': 'account.invoice',
            'datas': datas,
            'nodestroy': True,
            }

    def print_move(self, cr, uid, ids, context=None):
        '''
        cr: cursor de la base de datos
        uid: ID de usuario
        ids: lista ID del objeto instanciado

        Metodo para imprimir comprobante contable
        '''
        if not context:
            context = {}
        invoice = self.browse(cr, uid, ids, context)[0]
        datas = {'ids': [invoice.move_id.id], 'model': 'account.move'}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'report_move',
            'model': 'account.move',
            'datas': datas,
            'nodestroy': True,
            }

    def print_liq_purchase(self, cr, uid, ids, context=None):
        '''
        cr: cursor de la base de datos
        uid: ID de usuario
        ids: lista ID del objeto instanciado

        Metodo para imprimir reporte de liquidacion de compra
        '''
        if not context:
            context = {}
        invoice = self.browse(cr, uid, ids, context)[0]
        datas = {'ids': [invoice.id], 'model': 'account.invoice'}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'report_liq_purchase',
            'model': 'account.invoice',
            'datas': datas,
            'nodestroy': True,
            }

    def print_retention(self, cr, uid, ids, context=None):
        '''
        cr: cursor de la base de datos
        uid: ID de usuario
        ids: lista ID del objeto instanciado

        Metodo para imprimir reporte de retencion
        '''
        if not context:
            context = {}
        invoice = self.browse(cr, uid, ids, context)[0]
        datas = {'ids' : [invoice.retention_id.id],
                 'model': 'account.retention'}
        if invoice.retention_id:
            print datas
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.retention',
                'model': 'account.retention',
                'datas': datas,
                'nodestroy': True,
                }
        else:
            raise except_osv('Aviso', 'No tiene retención')

    def _amount_all(self, cr, uid, ids, fields, args, context=None):
        """
        Compute all total values in invoice object
        params:
        @cr cursor to DB
        @uid user id logged
        @ids active object ids
        @fields used fields in function, severals if use multi arg
        """
        res = {}
        cur_obj = self.pool.get('res.currency')

        invoices = self.browse(cr, uid, ids, context=context)
        for invoice in invoices:
            cur = invoice.currency_id
            res[invoice.id] = {
                'amount_vat': 0.0,
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_tax_retention': 0.0,
                'amount_tax_ret_ir': 0.0,
                'taxed_ret_ir': 0.0,
                'amount_tax_ret_vatb': 0.0,
                'amount_tax_ret_vatsrv': 0.00,
                'taxed_ret_vatb': 0.0,
                'taxed_ret_vatsrv': 0.00,
                'amount_vat_cero': 0.0,
                'amount_novat': 0.0,
                'amount_noret_ir': 0.0,
                'amount_total': 0.0,
                'amount_pay': 0.0,
                'amount_ice': 0.0
            }

            #Total General
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
            for line in invoice.tax_line:
                if line.type_ec == 'vat':
                    res[invoice.id]['amount_vat'] += line.base
                    res[invoice.id]['amount_tax'] += line.amount
                elif line.type_ec == 'vat0':
                    res[invoice.id]['amount_vat_cero'] += line.base
                elif line.type_ec == 'novat':
                    res[invoice.id]['amount_novat'] += line.base
                elif line.type_ec == 'no_ret_ir':
                    res[invoice.id]['amount_noret_ir'] += line.base
                elif line.type_ec in ['ret_vat_b', 'ret_vat_srv', 'ret_ir']:
                    res[invoice.id]['amount_tax_retention'] += line.amount
                    if line.type_ec == 'ret_vat_b':#in ['ret_vat_b', 'ret_vat_srv']:
                        res[invoice.id]['amount_tax_ret_vatb'] += line.base
                        res[invoice.id]['taxed_ret_vatb'] += line.amount
                    elif line.type_ec == 'ret_vat_srv':
                        res[invoice.id]['amount_tax_ret_vatsrv'] += line.base
                        res[invoice.id]['taxed_ret_vatsrv'] += line.amount
                    elif line.type_ec == 'ret_ir':
                        res[invoice.id]['amount_tax_ret_ir'] += line.base
                        res[invoice.id]['taxed_ret_ir'] += line.amount
                elif line.type_ec == 'ice':
                    res[invoice.id]['amount_ice'] += line.amount

            # base vat not defined, amount_vat_cero by default
            if res[invoice.id]['amount_vat'] == 0 and res[invoice.id]['amount_vat_cero'] == 0:
                res[invoice.id]['amount_vat_cero'] = res[invoice.id]['amount_untaxed']

            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed'] \
                                            + res[invoice.id]['amount_tax_retention']
            res[invoice.id]['amount_pay']  = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']

        return res

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        types = {
                'out_invoice': _('Invoice'),
                'in_invoice': _('Supplier Invoice'),
                'out_refund': _('Refund'),
                'in_refund': _('Supplier Refund'),
                'liq_purchase': _('Liquid. de Compra')
                }
        return [(r['id'], '%s %s' % (r['number'] or types[r['type']], r['name'] or '')) for r in self.read(cr, uid, ids, ['type', 'number', 'name'], context, load='_classic_write')]

    def _check_retention(self, cr, uid, ids, field_name, context, args):
        res = {}
        for inv in self.browse(cr, uid, ids, context):
            res[inv.id] = {
                'retention_ir': False,
                'retention_vat': False,
                'no_retention_ir': False,
                }
            for tax in inv.tax_line:
                if tax.type_ec in ['ret_vat_b', 'ret_vat_srv']:
                    res[inv.id]['retention_vat'] = True
                elif tax.type_ec == 'ret_ir':
                    res[inv.id]['retention_ir'] = True
                elif tax.type_ec == 'no_ret_ir':
                    res[inv.id]['no_retention_ir'] = True
        return res

    def _get_supplier_number(self, cr, uid, ids, fields, args, context):
        res = {}
        for inv in self.browse(cr, uid, ids, context):
            number = '/'
            if inv.type == 'in_invoice' and inv.auth_inv_id:
                n = inv.supplier_invoice_number and inv.supplier_invoice_number.zfill(9) or '*'
                number = ''.join([inv.auth_inv_id.serie_entidad,inv.auth_inv_id.serie_emision,n])
            res[inv.id] = number
        return res

    HELP_RET_TEXT = '''Automatico: El sistema identificara los impuestos y creara la retencion automaticamente, \
    Manual: El usuario ingresara el numero de retencion \
    Agrupar: Podra usar la opcion para agrupar facturas del sistema en una sola retencion.'''

    VAR_STORE = {
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            }

    PRECISION_DP = dp.get_precision('Account')

    _columns = {
        'supplier_number': fields.function(_get_supplier_number, method=True, type='char', size=32,
                                           string='Factura de Proveedor', store=True),
        'amount_ice': fields.function(_amount_all, method=True, digits_compute=PRECISION_DP, string='ICE',
                                      store=VAR_STORE, multi='all'),
        'amount_vat': fields.function(_amount_all, method=True,
                                      digits_compute=PRECISION_DP, string='Base 12 %',
                                      store=VAR_STORE,
                                      multi='all'),
        'amount_untaxed': fields.function(_amount_all, method=True,
                                          digits_compute=PRECISION_DP, string='Untaxed',
                                          store=VAR_STORE,
                                          multi='all'),
        'amount_tax': fields.function(_amount_all, method=True,
                                      digits_compute=PRECISION_DP, string='Tax',
                                      store=VAR_STORE,
                                      multi='all'),
        'amount_total': fields.function(_amount_all, method=True,
                                        digits_compute=PRECISION_DP, string='Total a Pagar',
                                        store=VAR_STORE,
                                        multi='all'),
        'amount_pay': fields.function(_amount_all, method=True,
                                      digits_compute=PRECISION_DP, string='Total',
                                      store=VAR_STORE,
                                      multi='all'),
        'amount_noret_ir': fields.function(_amount_all, method=True,
                                           digits_compute=PRECISION_DP, string='Monto no sujeto a IR',
                                           store=VAR_STORE,
                                           multi='all'),
        'amount_tax_retention': fields.function(_amount_all, method=True,
                                                digits_compute=PRECISION_DP, string='Total Retencion',
                                                store=VAR_STORE,
                                                multi='all'),
        'amount_tax_ret_ir': fields.function( _amount_all, method=True,
                                              digits_compute=PRECISION_DP, string='Base IR',
                                              store=VAR_STORE,
                                              multi='all'),
        'taxed_ret_ir': fields.function( _amount_all, method=True,
                                         digits_compute=PRECISION_DP, string='Impuesto IR',
                                         store=VAR_STORE,
                                         multi='all'),
        'amount_tax_ret_vatb' : fields.function( _amount_all,
                                                 method=True,
                                                 digits_compute=PRECISION_DP,
                                                 string='Base Ret. IVA',
                                                 store=VAR_STORE,
                                                 multi='all'),
        'taxed_ret_vatb' : fields.function( _amount_all,
                                            method=True,
                                            digits_compute=PRECISION_DP,
                                            string='Retencion en IVA',
                                            store=VAR_STORE,
                                            multi='all'),
        'amount_tax_ret_vatsrv' : fields.function( _amount_all,
                                                   method=True,
                                                   digits_compute=PRECISION_DP, string='Base Ret. IVA',
                                                   store=VAR_STORE,
                                                   multi='all'),
        'taxed_ret_vatsrv' : fields.function( _amount_all, method=True,
                                              digits_compute=PRECISION_DP,
                                              string='Retencion en IVA',
                                              store=VAR_STORE,
                                              multi='all'),
        'amount_vat_cero' : fields.function( _amount_all, method=True,
                                             digits_compute=PRECISION_DP, string='Base IVA 0%',
                                             store=VAR_STORE,
                                             multi='all'),
        'amount_novat' : fields.function( _amount_all, method=True,
                                          digits_compute=PRECISION_DP, string='Base No IVA',
                                          store=VAR_STORE,
                                          multi='all'),
        'create_retention_type': fields.selection([('normal','Automatico'),
                                                   ('manual', 'Manual'),
                                                   ('reserve','Num Reservado'),
                                                   ('no_retention', 'No Generar')],
                                                  string='Numerar Retención',
                                                  readonly=True,
                                                  help=HELP_RET_TEXT,
                                                  states = {'draft': [('readonly', False)]}),

        'auth_inv_id' : fields.many2one('account.authorisation', 'Autorización SRI',
                                        help = 'Autorizacion del SRI para documento recibido',
                                        readonly=True,
                                        states={'draft': [('readonly', False)]}),
        'retention_id': fields.many2one('account.retention', store=True,
                                        string='Retención de Impuestos',
                                        readonly=True),
        'retention_ir': fields.function(_check_retention, store=True,
                                         string="Tiene Retención en IR",
                                         method=True, type='boolean',
                                         multi='ret'),
        'retention_vat': fields.function(_check_retention, store=True,
                                          string='Tiene Retencion en IVA',
                                          method=True, type='boolean',
                                          multi='ret'),
        'no_retention_ir': fields.function(_check_retention, store=True,
                                          string='No objeto de Retención',
                                          method=True, type='boolean',
                                          multi='ret'),
        'type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ('liq_purchase','Liquidacion de Compra')
            ],'Type', readonly=True, select=True, change_default=True),
        'manual_ret_num': fields.integer('Num. Retención', readonly=True,
                                         states = {'draft': [('readonly', False)]}),
        'sustento_id': fields.many2one('account.ats.sustento',
                                       'Sustento del Comprobante'),
        }

    _defaults = {
        'create_retention_type': 'manual',
        }

    def onchange_journal_id(self, cr, uid, ids, journal_id=False, context=None):
        """
        Metodo redefinido para cargar la autorizacion de facturas de venta
        """
        result = {}
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
            currency_id = journal.currency and journal.currency.id or journal.company_id.currency_id.id
            company_id = journal.company_id.id

            if context.get('type') == 'out_invoice' and not journal.auth_id:
                return {
                    'warning': {
                        'title': 'Error',
                        'message': u'No se ha configurado una autorización en este diario.'
                        }
                    }
            result = {'value': {
                    'currency_id': currency_id,
                    'company_id': company_id,
                    'auth_inv_id': journal.auth_id.id
                    }
                }
        return result

    def _check_invoice_number(self, cr, uid, ids):
        """
        Metodo de validacion de numero de factura y numero de
        retencion

        numero de factura: suppplier_invoice_number
        numero de retencion: manual_ret_num
        """
        auth_obj = self.pool.get('account.authorisation')
        INV_MIN_LIMIT = 9  # CHECK: mover a compañia ?
        INV_MAX_LIMIT = 15
        LIMITS = [
            INV_MIN_LIMIT,
            INV_MAX_LIMIT
            ]

        for obj in self.browse(cr, uid, ids):
            if obj.state in ['open', 'paid', 'cancel']:
                return True
            if not len(obj.supplier_invoice_number) in LIMITS:
                raise osv.except_osv('Error', u'Son %s dígitos en el núm. de Factura.' % LIMITS)

            auth = obj.auth_inv_id

            inv_number = obj.supplier_invoice_number

            if len(obj.supplier_invoice_number) == INV_MAX_LIMIT:
                inv_number = obj.supplier_invoice_number[6:15]

            if not auth:
                raise osv.except_osv('Error', u'No se ha configurado una autorización de documentos, revisar Partner y Diario Contable.')

            if not auth_obj.is_valid_number(cr, uid, auth.id, int(inv_number)):
                raise osv.except_osv('Error', u'Número de factura fuera de rango.')

            # validacion de numero de retencion para facturas de proveedor
            if obj.type == 'in_invoice':
                if not obj.journal_id.auth_ret_id:
                    raise except_osv('Error', u'No ha cofigurado una autorización de retenciones.')

                if not auth_obj.is_valid_number(cr, uid, obj.journal_id.auth_ret_id.id, int(obj.manual_ret_num)):
                    raise osv.except_osv('Error', u'El número de retención no es válido.')
        return True

    _constraints = [
        (_check_invoice_number,
        u'Número fuera de rango de autorización activa.', ['Número Factura']),
    ]

    _sql_constraints = [
        ('unique_inv_supplier', 'unique(supplier_invoice_number,type,partner_id)', u'El número de factura es único.'),
    ]

    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(Invoice, self).copy_data(cr, uid, id, default, context=context)
        res.update({'reference': False,
                    'auth_inv_id': False,
                    'retention_id': False,
                    'supplier_invoice_number': False,
                    'manual_ret_num': False,
                    'retention_numbers': False})
        return res
    def onchange_partner_id(self, cr, uid, ids, type, partner_id,\
                    date_invoice=False, payment_term=False,
                    partner_bank_id=False, company_id=False, context=None):
        auth_obj = self.pool.get('account.authorisation')
        res1 = super(Invoice, self).onchange_partner_id(cr, uid, ids, type,
                                                        partner_id, date_invoice,
                                                        payment_term, partner_bank_id,
                                                        company_id)
        if res1['value'].has_key('reference_type'):
            res1['value'].pop('reference_type')
        res = auth_obj.search(cr, uid,
                [('partner_id','=',partner_id),('in_type','=','externo')],
                limit=1, context=context)
        if res:
            res1['value']['auth_inv_id'] = res[0]
        return res1

    def action_cancel_draft(self, cr, uid, ids, context):
        retention_obj = self.pool.get('account.retention')
        for inv in self.browse(cr, uid, ids, context):
            if inv.retention_id:
                retention_obj.unlink(cr, uid, [inv.retention_id.id], context)
        super(Invoice, self).action_cancel_draft(cr, uid, ids, context)
        return True

    def action_retention_create(self, cr, uid, ids, *args):
        '''
        @cr: DB cursor
        @uid: active ID user
        @ids: active IDs objects

        Este metodo genera el documento de retencion en varios escenarios
        considera casos de:
        * Generar retencion automaticamente
        * Generar retencion de reemplazo
        * Cancelar retencion generada
        '''
        context = args and args[0] or {}
        invoices = self.browse(cr, uid, ids)
        ret_obj = self.pool.get('account.retention')
        invtax_obj = self.pool.get('account.invoice.tax')
        ret_cache_obj = self.pool.get('account.retention.cache')
        ir_seq_obj = self.pool.get('ir.sequence')
        for inv in invoices:
            num_ret = False
            if inv.create_retention_type == 'no_retention':
                continue
            if inv.retention_id and not inv.retention_vat and not inv.retention_ir:
                num_next = inv.journal_id.auth_ret_id.sequence_id.number_next
                seq = inv.journal_id.auth_ret_id.sequence_id
                if num_next - 1 == int(inv.retention_id.name):
                    ir_seq_obj.write(cr, uid, seq.id, {'number_next': num_next-1})
                else:
                    ret_cache_obj.create(cr, uid, {'name': inv.retention_id.name})
            if inv.type in ['in_invoice', 'liq_purchase'] and (inv.retention_ir or inv.retention_vat):
                if inv.journal_id.auth_ret_id.sequence_id:
                    ret_data = {'name':'/',
                                'number': '/',
                                'invoice_id': inv.id,
                                'num_document': inv.supplier_number,
                                'auth_id': inv.journal_id.auth_ret_id.id,
                                'type': inv.type,
                                'in_type': 'ret_in_invoice',
                                'date': inv.date_invoice,
                                'period_id': inv.period_id.id
                                }
                    ret_id = ret_obj.create(cr, uid, ret_data)
                    for line in inv.tax_line:
                        pdb.set_trace()
                        if line.type_ec in ['ret_vat_b', 'ret_vat_srv', 'ret_ir']:
                            num = inv.supplier_number
                            invtax_obj.write(cr, uid, line.id, {'retention_id': ret_id, 'num_document': num})
                    if num_ret:
                        ret_obj.action_validate(cr, uid, [ret_id], num_ret)
                    elif inv.create_retention_type == 'normal':
                        ret_obj.action_validate(cr, uid, [ret_id])
                    elif inv.create_retention_type == 'manual':
                        if inv.manual_ret_num == 0:
                            raise osv.except_osv('Error', 'El número de retención es incorrecto.')
                        ret_obj.action_validate(cr, uid, [ret_id], inv.manual_ret_num)
                    elif inv.create_retention_type == 'reserve':
                        if inv.retention_numbers:
                            ret_num = ret_cache_obj.get_number(cr, uid, inv.retention_numbers)
                            ret_obj.action_validate(cr, uid, [ret_id], ret_num)
                        else:
                            raise osv.except_osv('Error', 'Corrija el método de numeración de la retención')
                    self.write(cr, uid, [inv.id], {'retention_id': ret_id})
                else:
                    raise osv.except_osv('Error de Configuracion',
                                         'No se ha configurado una secuencia para las retenciones en Compra')
        self._log_event(cr, uid, ids)
        return True

    def recreate_retention(self, cr, uid, ids, context=None):
        '''
        Metodo que implementa la recreacion de la retención
        TODO: recibir el numero de retención del campo manual
        '''
        if context is None:
            context = {}
        context.update({'recreate_retention': True})
        for inv in self.browse(cr, uid, ids, context):
            self.action_retention_cancel(cr, uid, [inv.id], context)
            self.action_retention_create(cr, uid, [inv.id], context)
        return True

    def action_retention_cancel(self, cr, uid, ids, *args):
        invoices = self.browse(cr, uid, ids)
        ret_obj = self.pool.get('account.retention')
        for inv in invoices:
            if inv.retention_id:
                ret_obj.action_cancel(cr, uid, [inv.retention_id.id])
        return True


class AccountInvoiceLine(osv.osv):
    _inherit = 'account.invoice.line'

    def move_line_get(self, cr, uid, invoice_id, context=None):
        res = []
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        if context is None:
            context = {}
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
        for line in inv.invoice_line:
            mres = self.move_line_get_item(cr, uid, line, context)
            if not mres:
                continue
            res.append(mres)
            tax_code_found= False
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id,
                    (line.price_unit * (1.0 - (line['discount'] or 0.0) / 100.0)),
                    line.quantity, line.product_id,
                    inv.partner_id)['taxes']:

                if inv.type in ('out_invoice', 'in_invoice', 'liq_purchase'):
                    tax_code_id = tax['base_code_id']
                    tax_amount = line.price_subtotal * tax['base_sign']
                else:
                    tax_code_id = tax['ref_base_code_id']
                    tax_amount = line.price_subtotal * tax['ref_base_sign']

                if tax_code_found:
                    if not tax_code_id:
                        continue
                    res.append(self.move_line_get_item(cr, uid, line, context))
                    res[-1]['price'] = 0.0
                    res[-1]['account_analytic_id'] = False
                elif not tax_code_id:
                    continue
                tax_code_found = True

                res[-1]['tax_code_id'] = tax_code_id
                res[-1]['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, tax_amount, context={'date': inv.date_invoice})
        return res


class AccountInvoiceRefund(osv.TransientModel):

    _inherit = 'account.invoice.refund'

    def _get_description(self, cr, uid, context=None):
        number = '/'
        if not context.get('active_id'):
            return number
        invoice = self.pool.get('account.invoice').browse(cr, uid, context.get('active_id'))
        if invoice.type == 'out_invoice':
            number = invoice.number
        else:
            number = invoice.supplier_number
        return number

    _defaults = {
        'description': _get_description,
        }

