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

class account_check_delay(osv.osv_memory):
    """
        close period
    """
    _name = "account.check.delay"
    _description = "Check delay"
    _columns = {
        'delay_checks': fields.one2many('account.check.delay.line', string="Delayed Checks"),
    }

    def delay_checks(self, cr, uid, ids, context=None):
        """
        This function close period
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: account period close’s ID or list of IDs
         """
        period_pool = self.pool.get('account.period')
        account_move_obj = self.pool.get('account.move')

        mode = 'done'
        for delay_check_id in self.read(cr, uid, ids, context=context):
            if form['sure']:
                for id in context['active_ids']:
                    account_move_ids = account_move_obj.search(cr, uid, [('period_id', '=', id), ('state', '=', "draft")], context=context)
                    if account_move_ids:
                        raise osv.except_osv(_('Invalid Action!'), _('In order to close a period, you must first post related journal entries.'))

                    cr.execute('update account_journal_period set state=%s where period_id=%s', (mode, id))
                    cr.execute('update account_period set state=%s where id=%s', (mode, id))

        return {'type': 'ir.actions.act_window_close'}

account_check_delay()

class account_check_delay_line(osv.osv_memory):
    _name = "account.check.delay.line"
    _description = "Check delay line"
    _columns = {
        'wizard_id': fields.many2one('account.check.delay', string="Wizard"),
        'number':,
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: