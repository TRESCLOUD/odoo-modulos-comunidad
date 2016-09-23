# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2016 TRESCLOUD Cia Ltda (www.trescloud.com)
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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import date, datetime
import time


class wizard_rejected_check(osv.osv_memory):
    _name = 'wizard.rejected.check'
    
    def onchange_entry_date_rejected(self, cr, uid, ids, entry_date_rejected, context=None):
        '''
        Este método setea la fecha de contabilizacion
        :param cr: Cursor estándar de base de datos de PostgreSQL
        :param uid: ID del usuario actual
        :param ids: IDs del wizard
        :param entry_date_rejected: Fecha de documento
        :param context: Diccionario de datos de contexto adicional 
        '''
        if context is None:
            context = {}
        vals = {'value': {}, 'warning': {}, 'domain': {}}
        if entry_date_rejected:
            vals['value'].update({'date_rejected': entry_date_rejected})
        return vals  

    def action_approve(self, cr, uid, ids, context=None):
        '''
        Este método crea los apuntes contables para el asiento de reverso cuando se protesta un cheque
        :param cr: Cursor estándar de base de datos de PostgreSQL
        :param uid: ID del usuario actual
        :param ids: IDs del wizard
        :param context: Diccionario de datos de contexto adicional 
        '''
        if context is None:
            context = {}       
        if context.get('active_id'):
            move = {}
            move_line_debit = {}
            move_line_credit = {}
            voucher_id = context.get('active_id')
            account_move_obj = self.pool.get('account.move')
            account_move_line_obj = self.pool.get('account.move.line')
            account_voucher_obj = self.pool.get('account.voucher')
            wizard = self.browse(cr, uid, ids[0], context=context)
            if context.get('origin') == 'multi_reject_checks':
                wizard = self.pool.get('account.check.reject.line').browse(cr, uid, ids[0], context=context)
                voucher_id = wizard.voucher_id.id
            voucher = account_voucher_obj.browse(cr, uid, voucher_id, context=context)
            #Asiento contable
            move.update({
                'journal_id': voucher.journal_id.id, 
                'period_id': voucher.period_id.id, 
                'date': wizard.date_rejected, 
                'description': wizard.note
            })
            move_id = account_move_obj.create(cr, uid, move, context=context)
            #Apunte contable de débito
            account_id = False
            if voucher.journal_id.default_invalid_checks_acc_id:
                account_id = voucher.journal_id.default_invalid_checks_acc_id.id
            else:
                account_id = voucher.partner_id.property_account_receivable.id
            move_line_debit.update({
                'account_id': account_id, 
                'period_id': voucher.period_id.id, 
                'date': wizard.date_rejected, 
                'partner_id': voucher.partner_id.id, 
                'move_id': move_id, 
                'name': u'Protesto del Cheque Nro: ' + str(voucher.check_number),
                'journal_id': voucher.journal_id.id, 
                'credit': 0.0, 
                'debit': voucher.amount,
            })
            move_line_debit_id = account_move_line_obj.create(cr, uid, move_line_debit, context=context)
            #Apunte contable de crédito
            move_line_credit.update({
                'account_id': voucher.account_id.id, 
                'period_id': voucher.period_id.id, 
                'date': wizard.date_rejected, 
                'partner_id': voucher.partner_id.id, 
                'move_id': move_id, 
                'name': u'Protesto del Cheque Nro: ' + str(voucher.check_number),
                'journal_id': voucher.journal_id.id,
                'credit': voucher.amount, 
                'debit': 0.0, 
            })
            move_line_credit_id = account_move_line_obj.create(cr, uid, move_line_credit, context=context)
            account_voucher_obj.write(cr, uid, [voucher_id], {
                'state_check_control': 'rejected_check',
                'entry_date_rejected': wizard.entry_date_rejected, 
                'date_rejected': wizard.date_rejected,
                'rejected_move_id': move_id
            }, context=context)
        return True

    _columns = {
        'entry_date_rejected': fields.date('Document Date', 
                                           help='The date of the document support if any (eg complaint to deregister a stolen good)'),
        'date_rejected': fields.date('Accounting Date', 
                                     help='The date of involvement based accounting which affects the balance of the company'),
        'note': fields.text('Reject Reason', help='Write the reason which the check reject')
    }
    
    _defaults = {
        'entry_date_rejected': lambda *a: time.strftime('%Y-%m-%d'),
        'date_rejected': lambda *a: time.strftime('%Y-%m-%d')
    }

wizard_rejected_check()
