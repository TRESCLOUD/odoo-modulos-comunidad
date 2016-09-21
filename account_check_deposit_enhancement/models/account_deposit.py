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

from openerp.osv import fields, orm
from openerp.tools.translate import _


class account_check_deposit(orm.Model):
    _inherit = "account.check.deposit"

    def validate_deposit(self, cr, uid, ids, context=None):
        '''
        Valida el deposito, Cambia de estado el pago a cheques depositados.
        :param ids: Ids del deposito
        :param context: Variables de contexto o de ambiente
        '''
        context = context or {}
        super(account_check_deposit, self).validate_deposit(cr, uid, ids, context=context)
        am_obj = self.pool['account.move']
        aml_obj = self.pool['account.move.line']
        av_obj = self.pool.get('account.voucher')
        for deposit in self.browse(cr, uid, ids, context=context):
            line_ids = [line.id for line in deposit.check_payment_ids]
            account_move_searched = am_obj.search(cr, uid, [('line_id', 'in', line_ids)], context=context)
            account_voucher_searched = av_obj.search(cr, uid, [('move_id', 'in', account_move_searched)], context=context)
            if account_voucher_searched:
                av_obj.write(cr, uid, account_voucher_searched, {'state_check_control': 'deposited_check'})
        return True

account_check_deposit()
