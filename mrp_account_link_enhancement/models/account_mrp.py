# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2016 TRESCLOUD Cia Ltda (trescloud.com)
#    All Rights Reserved.
############################################################################
#    Coded by: Santiago Orozco (santiago.orozco@trescloud.com)
############################################################################
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

from tools.translate import _
from openerp.osv import osv, fields


class mrp_production(osv.Model):
    
    _name = 'mrp.production'
    _inherit = ['mail.thread', "mrp.production"]
    
    def action_account_reprocess(self, cr, uid, ids, context=None):
        '''
        Reprocesamiento de asientos contables de ordenes de produccion
        :param cr: Cursor de la base de datos
        :param uid: Id de usuario para la transaccion
        :param ids: Ids de las ordenes de produccion
        :param context: Variables de contexto como zona horaria, lenguaje, etc
        '''
        account_move_line_obj = self.pool.get('account.move.line')
        account_move_obj = self.pool.get('account.move')
        stock_move_obj = self.pool.get('stock.move')
        # Buscamos las lineas los asientos contables asociados a la orden de produccion
        journal_items_ids = account_move_line_obj.search(cr, uid, [('production_id','in', ids if isinstance(ids, (list,tuple)) else [ids])],context=context)
        # Buscamos los asientos contables asociados a la orden de produccion
        journal_entries_ids = list(set([journal_item.move_id.id for journal_item in account_move_line_obj.browse(cr, uid, journal_items_ids, context=context)]))
        # Eliminamos los apuntes contables
        account_move_line_obj.unlink(cr, uid, journal_items_ids, context=context)
        # Cancelamos los asientos contables
        account_move_obj.button_cancel(cr, uid, journal_entries_ids, context=context)
        # Eliminamos los asientos contables
        journal_entries_ids = account_move_obj.unlink(cr, uid, journal_entries_ids, context=context)
        # Regeneramos los asientos contables y los apuntes
        for production in self.browse(cr, uid, ids, context=context):
            for move in production.move_lines2:
                stock_move_obj._create_product_valuation_moves(cr, uid, move, context=context)
            extra_info = ''
            if production.state == 'done':
                extra_info = "\n\nEl costo del producto debe ser actualizado manualmente por el usuario." 

            message = _("La orden de producción número %s ha sido reprocesada por %s." + extra_info
                        ) %(production.name, self.pool.get('res.users').browse(cr, uid, uid, context=context).name)
            self.message_post(cr, uid, production.id,
                        body=message,
                        subtype='mail.mt_comment',
                        context=context)
        return True
    

mrp_production()

class stock_move(osv.osv):
    
    _inherit = "stock.move"
    
    def _create_account_move_line(self, cr, uid, move, src_account_id, dest_account_id, reference_amount, reference_currency_id, context=None):
        '''
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given stock move.
        :param cr: Cursor de la base de datos
        :param uid: Id de usuario para la transaccion
        :param ids: Records de las lineas de movimiento
        :param src_account_id: Cuenta contable de origen
        :param dest_account_id: Cuenta contable de destino
        :param reference_amount: Monto de la transaccion
        :param reference_currency_id: Id de la moneda de transaccion
        :param context: Variables de contexto como zona horaria, lenguaje, etc
        '''
        result = super(stock_move, self)._create_account_move_line(cr, uid, move, src_account_id, dest_account_id, reference_amount, reference_currency_id, context=context)
        for (opcode, id, debit_line_vals) in result:
            debit_line_vals.update({'date': move.date})
        return result


stock_move()