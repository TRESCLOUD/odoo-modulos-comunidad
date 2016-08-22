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

class account_check_from_till(osv.osv_memory):

    _name = "account.check.till"
    _description = "Check from till"

    def till_checks(self, cr, uid, ids, context=None):
        """
        Este metodo sirve para recibir los cheques de caja.
        Cambia de estado el voucher
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: account period close’s ID or list of IDs
         """
        account_voucher_obj = self.pool.get('account.voucher')

        for from_till_check_id in self.read(cr, uid, ids, context=context):
            for id in context['active_ids']:
                account_voucher_ids = account_voucher_obj.write(cr, uid, id, {'state_check_control': 'received_check'}, context=context)

        return {'type': 'ir.actions.act_window_close'}

account_check_from_till()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: