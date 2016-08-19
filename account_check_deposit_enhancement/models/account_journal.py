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

from osv import fields,osv
from tools.translate import _


class account_journal(osv.osv):
    _name = 'account.journal'
    _inherit = ['account.journal','mail.thread']   
    
    _columns = {
                'default_invalid_checks_acc_id': fields.many2one('account.account', 
                                                                 'Invalid checks account',
                                                                 track_visibility='onchange',
                                                                 help="Default account for registring the moves for invalid checks."
                                                                 ),
                'control_customer_check': fields.boolean('Control customer checks',
                                                         track_visibility='onchange',
                                                         help="This field allows to control and manage the checks that your customers write for paying their debts."
                                                         ),
                'deposit_management': fields.boolean('Deposit Management',
                                                     track_visibility='onchange',
                                                     help="This field allows to the system identify if this journal will manage the deposits for checks."
                                                     ),
                }
    
    
account_journal()