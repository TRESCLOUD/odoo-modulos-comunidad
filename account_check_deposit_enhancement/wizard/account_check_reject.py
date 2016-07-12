# -*- coding: UTF-8 -*- #
########################################################################
#                                                                                                                                              
# Copyright (C) 2015  TRESCLOUD CIA. LTDA.                                 
#                                                                       
#This program is free software: you can redistribute it and/or modify   
#it under the terms of the GNU General Public License as published by   
#the Free Software Foundation, either version 3 of the License, or      
#(at your option) any later version.                                    
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#                                                                       
#This program is distributed in the hope that it will be useful,        
#but WITHOUT ANY WARRANTY; without even the implied warranty of         
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          
#GNU General Public License for more details.                           
#                                                                       
#You should have received a copy of the GNU General Public License      
#along with this program.  If not, see http://www.gnu.org/licenses.
########################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
import time

class account_check_reject(osv.osv_memory):
    _name = "account.check.reject"
    _description = "Check reject"
    
    def _partial_voucher_for(self, cr, uid, voucher, context=None):
        partial_move = {
            'check_number': voucher.number,
            'amount': voucher.amount or 0,
            'partner_id': voucher.partner_id.id,
            'old_deposit_date': voucher.deposit_date,
            'voucher_id': voucher.id,
        }
        return partial_move
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        # no call to super!
        res = {}
        voucher_obj = self.pool.get('account.voucher')
        voucher_ids = context.get('active_ids', False)
        if not voucher_ids or not context.get('active_model') == 'account.voucher':
            return res
        if 'reject_checks' in fields:
            voucher_ids = voucher_obj.browse(cr, uid, voucher_ids, context=context)
            vouchers = [self._partial_voucher_for(cr, uid, m, context=context) for m in voucher_ids]
            res.update(reject_checks=vouchers)
        return res
   
    def reject_checks(self, cr, uid, ids, context=None):
        """
        This function close period
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: account period close’s ID or list of IDs
         """
        account_voucher_obj = self.pool.get('account.voucher')
        for rejected_check_id in self.browse(cr, uid, ids, context=context):
            if context.get('active_model') == 'account.voucher':
                for line_id in rejected_check_id.reject_checks:
                    note = line_id.note
                    voucher_id = line_id.voucher_id.id
                    account_voucher_obj.write(cr, uid, voucher_id, {'rejected_reason': note,
                                                                    'state_check_control': 'rejected_check'}, context=context)

        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'reject_checks': fields.one2many('account.check.reject.line', 'wizard_id',string="Rejected Checks", help=""),
    }


account_check_reject()

class account_check_reject_line(osv.osv_memory):
    _name = "account.check.reject.line"
    _description = "Check reject line"
    
    _columns = {
        'wizard_id': fields.many2one('account.check.reject', string="Wizard"),
        'check_number': fields.char('Check number', help=""),
        'amount': fields.float('Amount', help=""),
        'partner_id': fields.many2one('res.partner', string='Partner',help=""),
        'old_deposit_date': fields.date('Old Deposit Date', help=""),
        'note': fields.text('Reject Reason', help=""),
        'voucher_id': fields.many2one('account.voucher', string='Voucher', help=""),
    }


account_check_reject_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: