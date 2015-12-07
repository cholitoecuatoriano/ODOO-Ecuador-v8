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

from openerp import models, fields, api, _
import pdb


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def action_number(self):
        """
        Copied from account.invoice in odoo addons
        """
        #TODO: not correct fix but required a fresh values before reading it.
        self.write({})

        for inv in self:
            data_number = {'internal_number': inv.number}

            if inv.type in ('out_invoice', 'liq_purchase'):
                ref = inv.number
                data_number = {'internal_number': ref}
                auth = inv.journal_id.auth_id
                number = inv.internal_number
                if not number:
                    tmp_number = self.env['ir.sequence'].next_by_id(auth.sequence_id.id)
                    number = '{0}-{1}-{2}'.format(auth.serie_entidad, auth.serie_emision, tmp_number)
                data_number.update({'supplier_invoice_number': number})
                self.write(data_number)

            if inv.type in ('in_invoice', 'in_refund'):
                if not inv.reference:
                    ref = inv.number
                else:
                    ref = inv.reference
            else:
                ref = inv.number

            self._cr.execute(""" UPDATE account_move SET ref=%s
                           WHERE id=%s AND (ref IS NULL OR ref = '')""",
                        (ref, inv.move_id.id))
            self._cr.execute(""" UPDATE account_move_line SET ref=%s
                           WHERE move_id=%s AND (ref IS NULL OR ref = '')""",
                        (ref, inv.move_id.id))
            self._cr.execute(""" UPDATE account_analytic_line SET ref=%s
                           FROM account_move_line
                           WHERE account_move_line.move_id = %s AND
                                 account_analytic_line.move_id = account_move_line.id""",
                        (ref, inv.move_id.id))
            self.invalidate_cache()

        return True

#    def action_number(self, cr, uid, ids, context=None):
#        """
#        Copiado el metodo del ERP
#        CHECK: modificar para numeracion automatica en venta?
#        """
#        if context is None:
#            context = {}
#        #TODO: not correct fix but required a frech values before reading it.
#        self.write(cr, uid, ids, {})
#
#        for obj_inv in self.browse(cr, uid, ids, context=context):
#            invtype = obj_inv.type
#            number = obj_inv.number
#            data_number = {'internal_number': number}
#            if invtype in ['out_invoice', 'liq_purchase']:
#                auth = obj_inv.journal_id.auth_id
#                number = obj_inv.internal_number
#                if not number:
#                    tmp_number = self.pool.get('ir.sequence').get_id(cr, uid, auth.sequence_id.id)
#                    number = '{0}{1}{2}'.format(auth.serie_entidad, auth.serie_emision, tmp_number)
#                data_number.update({'supplier_invoice_number': number})
#
#            move_id = obj_inv.move_id and obj_inv.move_id.id or False
#            reference = obj_inv.reference or ''
#
#            self.write(cr, uid, ids, data_number)
#
#            if invtype in ('in_invoice', 'in_refund'):
#                if not reference:
#                    ref = self._convert_ref(cr, uid, number)
#                else:
#                    ref = reference
#            else:
#                ref = self._convert_ref(cr, uid, number)
#
#            cr.execute('UPDATE account_move SET ref=%s ' \
#                    'WHERE id=%s AND (ref is null OR ref = \'\')',
#                    (ref, move_id))
#            cr.execute('UPDATE account_move_line SET ref=%s ' \
#                    'WHERE move_id=%s AND (ref is null OR ref = \'\')',
#                    (ref, move_id))
#            cr.execute('UPDATE account_analytic_line SET ref=%s ' \
#                    'FROM account_move_line ' \
#                    'WHERE account_move_line.move_id = %s ' \
#                        'AND account_analytic_line.move_id = account_move_line.id',
#                        (ref, move_id))
#        return True


