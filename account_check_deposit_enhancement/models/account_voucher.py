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
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class account_voucher(osv.osv):
    _inherit = 'account.voucher'

    _STATES_CHECKS=[('got_check','Cheques Receptados Caja'),
                    ('received_check','Cheques Recibido'),
                    ('deposited_check','Cheques Depositado'),
                    ('rejected_check','Cheques Protestado'),
                    ('delayed_check','Cheques Detenidos')]
    
    def _get_invoice(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, {'invoice_payed': '', 'check_deposit_id': False})
        for voucher_id in self.browse(cr, uid, ids, context=context):
            for line in voucher_id.line_cr_ids:
                if line.move_line_id:
                    res[voucher_id.id]['check_deposit_id'] = line.move_line_id.check_deposit_id.id
                    if line.move_line_id.invoice:
                        res[voucher_id.id]['invoice_payed'] += line.move_line_id.invoice.internal_number or '' +'\n'
                        continue
        return res
    
    _columns = {
        'check_manage': fields.boolean('Check manage'),
        'bank_account_partner_id': fields.many2one('res.partner.bank', 'Number account', help=""),
        'check_deposit_id': fields.function(_get_invoice, relation="account.check.deposit", store=True,
                                            type='many2one', multi='calc', string='Check Deposit', 
                                            readonly=True),
        'deposit_date': fields.date('Deposit Date', help=""),
        'new_deposit_date': fields.date('Deposit Date', help=""),
        'state_check_control': fields.selection(_STATES_CHECKS, 'State control checks', help=""),
        'rejected_reason': fields.char('Rejected reason', help=""),
        'invoice_payed': fields.function(_get_invoice, method=True, type='char', 
                                         multi='calc', string='Payed Invoices'),
    }
    
    _defaults = {'state_check_control': 'got_check'}
    
    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        if not context:
            context = {}            
        default = super(account_voucher, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=context)
        if default and default.get('value',False):
            journal_obj = self.pool.get('account.journal')
            journal = None            
            allow = False
            if journal_id:
                journal = journal_obj.browse(cr, uid, journal_id, context=context)
                allow = journal.control_customer_check
            if ttype == 'receipt':
                default['value'].update({'check_manage': allow})
        return default

account_voucher()