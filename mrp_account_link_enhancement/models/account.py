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


from openerp.osv import osv, fields


class mrp_production(osv.Model):
    
    _inherit = "mrp.production"
    
    def action_account_reprocess(self, cr, uid, ids, context=None):
        account_move_line_obj = self.pool.get('account.move.line')
        account_move_obj = self.pool.get('account.move')
        stock_move_obj = self.pool.get('stock.move')
        journal_items_ids = account_move_line_obj.search(cr, uid, [('production_id','in', ids if isinstance(ids, (list,tuple)) else [ids])],context=context)
        journal_entries_ids = list(set([journal_item.move_id.id for journal_item in account_move_line_obj.browse(cr, uid, journal_items_ids, context=context)]))
        account_move_line_obj.unlink(cr, uid, journal_items_ids, context=context)
        account_move_obj.button_cancel(cr, uid, journal_entries_ids, context=context)
        journal_entries_ids = account_move_obj.unlink(cr, uid, journal_entries_ids, context=context)
        for production in self.browse(cr, uid, ids, context=context):
            for move in production.move_lines2:
                stock_move_obj._create_product_valuation_moves(cr, uid, move, context=context)
        return True
    

mrp_production()
