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


class account_check_reject(osv.osv_memory):
    _name = "account.check.reject"
    _description = "Check reject"
    
    def _partial_voucher_for(self, cr, uid, voucher, context=None):
        '''
        Prepara la vista de los cheques que van a ser protestados
        :param voucher: Cheque que se depositara
        :param context: Variables de contexto
        '''
        partial_move = {
            'check_number': voucher.check_number,
            'amount': voucher.amount or 0,
            'partner_id': voucher.partner_id.id,
            'old_deposit_date': voucher.deposit_date,
            'voucher_id': voucher.id,
            'entry_date_rejected': time.strftime('%Y-%m-%d'),
            'date_rejected': time.strftime('%Y-%m-%d'),
        }
        return partial_move
    
    def default_get(self, cr, uid, fields, context=None):
        '''
        Se carga los campos por defecto en el asistente
        para ser protestados los cheques
        :param fields: Campos que seran analizados
        :param context: Variables de contexto o de ambiente
        '''
        if context is None: context = {}
        res = super(account_check_reject, self).default_get(cr, uid, fields, context=context)
        voucher_obj = self.pool.get('account.voucher')
        voucher_ids = context.get('active_ids', False)
        # Si no estamos en account.voucher entonces no hacemos nada
        if not voucher_ids or not context.get('active_model') == 'account.voucher':
            return res
        # Si el campo por defecto que requerimos esta en los pendientes
        # entonces se analiza las lineas seleccionadas y se las carga 
        # en el asistente
        if 'reject_checks' in fields:
            voucher_ids = voucher_obj.browse(cr, uid, voucher_ids, context=context)
            vouchers = [self._partial_voucher_for(cr, uid, m, context=context) for m in voucher_ids]
            res.update(reject_checks=vouchers)
        return res
   
    def reject_checks(self, cr, uid, ids, context=None):
        """
        Cheques protestados por el usuario
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: account period close’s ID or list of IDs
        @param context: Variables de contexto o de ambiente
        """
        if context is None:
            context = {}
        context.update({'origin': 'multi_reject_checks'})
        wizard = self.browse(cr, uid, ids[0], context=context)
        for line in wizard.reject_checks:
            self.pool.get('wizard.rejected.check').action_approve(cr, uid, [line.id], context=context)
        return True

    _columns = {
        'reject_checks': fields.one2many('account.check.reject.line', 'wizard_id',string="Rejected Checks", help=""),
    }

account_check_reject()


class account_check_reject_line(osv.osv_memory):
    _name = "account.check.reject.line"
    _description = "Check reject line"
        
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
    
    _columns = {
        'wizard_id': fields.many2one('account.check.reject', string="Wizard"),
        'check_number': fields.char('Check number', help="Check Number from the customer"),
        'amount': fields.float('Amount', help="Amount of the check"),
        'partner_id': fields.many2one('res.partner', string='Partner',help="Customer of the check"),
        'old_deposit_date': fields.date('Old Deposit Date', help="Previous Date of the deposit"),
        'note': fields.text('Reject Reason', help="Reason for what the check is rejected"),
        'voucher_id': fields.many2one('account.voucher', string='Voucher', help=""),
        'entry_date_rejected': fields.date('Document Date', 
                                           help='The date of the document support if any (eg complaint to deregister a stolen good)'),
        'date_rejected': fields.date('Accounting Date', 
                                     help='The date of involvement based accounting which affects the balance of the company'),
    }

account_check_reject_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: