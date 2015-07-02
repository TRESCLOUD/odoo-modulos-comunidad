# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.be). All rights reserved.
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

import time
from report import report_sxw
from osv import osv
#import logging
#_logger = logging.getLogger(__name__)

class move_line_list_print(report_sxw.rml_parse):
           
    def __init__(self, cr, uid, name, context):
        super(move_line_list_print, self).__init__(cr, uid, name, context=context)
        self.context = context
        self.localcontext.update({
            'time': time,
            'cr': cr,
            'uid': uid,
            'lang': context.get('lang', 'en_US'),
            'name_get': self._name_get,
        })

    def set_context(self, objects, data, ids, report_type=None):
        cr = self.cr
        uid = self.uid
        context = self.context
        self.localcontext.update( {
            'sum_debit': self._sum_debit(ids),           
            'sum_credit': self._sum_credit(ids),           
        })
        super(move_line_list_print, self).set_context(objects, data, ids, report_type=report_type)

    def _sum_debit(self, ids):
        self.cr.execute('SELECT sum(debit) FROM account_move_line WHERE id IN %s',(tuple(ids),))
        return self.cr.fetchone()[0] or 0.0        

    def _sum_credit(self, ids):
        self.cr.execute('SELECT sum(credit) FROM account_move_line WHERE id IN %s',(tuple(ids),))
        return self.cr.fetchone()[0] or 0.0  
    
    def _name_get(self, object):
        res = self.pool.get(object._name).name_get(self.cr, self.uid, [object.id], self.context)
        return res[0][1]

# OJO aca
# report_sxw.report_sxw('report.move.line.list.print', 'account.move.line', 'addons/account_move_line_report/report/move_line_list_print.mako', parser=move_line_list_print)
