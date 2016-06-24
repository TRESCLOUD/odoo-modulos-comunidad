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


    _columns = {
        'check_manage': fields.related('journal_id', 'control_customer_check', string='Check manage',
                                       type='boolean',
                                       readonly=True,
                                       relation='account.journal',
                                       help='This field stores the errors generated when processing documents'),
        'check_manage_prueba': fields.boolean('Check manage'),
        'bank_account_partner_id': fields.many2one('res.partner.bank', 'Number account', help=""),
        'deposit_date': fields.date('Deposit Date', help="")
    }

    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        """
        Inherit the on_change from account.voucher, add allow_check_writing and sequence check
        """
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