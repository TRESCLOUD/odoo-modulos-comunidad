# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010-2014 Elico Corp. All Rights Reserved.
#    Alex Duan <alex.duan@elico-corp.com>
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
from openerp.osv import orm, fields
from openerp import netsvc
from openerp.tools.translate import _


class stock_location(orm.Model):
    _inherit = 'stock.location'

    _columns = {
        'is_in_average': fields.boolean(
            'Accounts for Average Price calculation',
            help='Check this box if you want to take into account the stock of'
            ' this location '
            'the average stock calculation')
    }

    _defaults = {
        'is_in_average': True
    }

    def get_product_qty_of_checked_locations(
        self, cr, uid,
            id, product_ids=False, domain=None, context=None, states=None):
        if isinstance(product_ids, (int, long)):
            product_ids = [product_ids]
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company_id = user_obj.company_id
        domain = domain or []
        domain.extend([
            ('is_in_average', '=', True),
            ('usage', '=', 'internal'),
            ('active', '=', True),
            ('company_id', 'in', (company_id and company_id.id or False, False, None))])
        states = states or ['done']
        location_obj = self.pool.get('stock.location')
        ids = id and [id] or []
        location_ids = location_obj.search(
            cr, uid, domain, context=context)
        # don't calculate the children location ids.
        context['compute_child'] = False
        # we don't minus the outgoing amount.
        what = ('in', 'out')
        #TODO check if we have duplicated location ids.
        if not location_ids:
            return {}.fromkeys(product_ids, 0.0)
        res = self._product_get_multi_location(
            cr, uid, location_ids, product_ids, context, states, what)
        return res


class stock_move(orm.Model):
    _inherit = 'stock.move'
    
    #===========================================================================
    # ESTE CODIGO ES COMENTADO DEBIDO A QUE NO SE TIENE QUE RECALCULAR
    # EL COSTO DEL PRODUCTO
    #===========================================================================

    # FIXME: needs refactoring, this code is partially duplicated in stock_picking.do_partial()!
#===============================================================================
#     def do_partial(self, cr, uid, ids, partial_datas, context=None):
#         """ Makes partial pickings and moves done.
#         @param partial_datas: Dictionary containing details of partial picking
#                           like partner_id, delivery_date, delivery
#                           moves with product_id, product_qty, uom
#         """
#         res = {}
#         picking_obj = self.pool.get('stock.picking')
#         product_obj = self.pool.get('product.product')
#         currency_obj = self.pool.get('res.currency')
#         location_obj = self.pool.get('stock.location')
#         uom_obj = self.pool.get('product.uom')
#         wf_service = netsvc.LocalService("workflow")
# 
#         if context is None:
#             context = {}
# 
#         complete, too_many, too_few = [], [], []
#         move_product_qty = {}
#         prodlot_ids = {}
#         for move in self.browse(cr, uid, ids, context=context):
#             if move.state in ('done', 'cancel'):
#                 continue
#             partial_data = partial_datas.get('move%s' % (move.id), False)
#             assert partial_data, _(
#                 'Missing partial picking data for move #%s.') % (move.id)
#             product_qty = partial_data.get('product_qty', 0.0)
#             move_product_qty[move.id] = product_qty
#             product_uom = partial_data.get('product_uom', False)
#             product_price = partial_data.get('product_price', 0.0)
#             product_currency = partial_data.get('product_currency', False)
#             prodlot_ids[move.id] = partial_data.get('prodlot_id')
#             if move.product_qty == product_qty:
#                 complete.append(move)
#             elif move.product_qty > product_qty:
#                 too_few.append(move)
#             else:
#                 too_many.append(move)
# 
#             # <<<< change begin <<<<<<<<<<
#             # get the qty of available Alex
#             product_qty_available = location_obj.get_product_qty_of_checked_locations(
#                 cr, uid, [],
#                 move.product_id.id, context=context, states=['done']).get(
#                 move.product_id.id, 0.0)
#             # <<<< change ends <<<<<<<<<<<<
# 
#             # Average price computation
#             if (move.picking_id.type == 'in') and (move.product_id.cost_method == 'average'):
#                 product = product_obj.browse(cr, uid, move.product_id.id)
#                 move_currency_id = move.company_id.currency_id.id
#                 context['currency_id'] = move_currency_id
#                 qty = uom_obj._compute_qty(cr, uid, product_uom, product_qty, product.uom_id.id)
#                 if qty > 0:
#                     new_price = currency_obj.compute(
#                         cr, uid, product_currency,
#                         move_currency_id, product_price)
#                     new_price = uom_obj._compute_price(
#                         cr, uid, product_uom, new_price,
#                         product.uom_id.id)
#                     if product_qty_available <= 0:
#                         new_std_price = new_price
#                     else:
#                         # Get the standard price
#                         amount_unit = product.price_get(
#                             'standard_price', context=context)[product.id]
#                         new_std_price = ((
#                             amount_unit * product_qty_available) +
#                             (new_price * qty)) / (product_qty_available + qty)
# 
#                     product_obj.write(
#                         cr, uid, [product.id],
#                         {'standard_price': new_std_price})
# 
#                     # Record the values that were chosen in the wizard,
#                     # so they can be used for inventory valuation if
#                     # real-time valuation is enabled.
#                     self.write(
#                         cr, uid, [move.id],
#                         {'price_unit': product_price,
#                          'price_currency_id': product_currency,
#                          })
# 
#         for move in too_few:
#             product_qty = move_product_qty[move.id]
#             if product_qty != 0:
#                 defaults = {
#                     'product_qty': product_qty,
#                     'product_uos_qty': product_qty,
#                     'picking_id': move.picking_id.id,
#                     'state': 'assigned',
#                     'move_dest_id': False,
#                     'price_unit': move.price_unit,
#                 }
#                 prodlot_id = prodlot_ids[move.id]
#                 if prodlot_id:
#                     defaults.update(prodlot_id=prodlot_id)
#                 new_move = self.copy(cr, uid, move.id, defaults)
#                 complete.append(self.browse(cr, uid, new_move))
#             self.write(
#                 cr, uid, [move.id],
#                 {
#                     'product_qty': move.product_qty - product_qty,
#                     'product_uos_qty': move.product_qty - product_qty,
#                     'prodlot_id': False,
#                     'tracking_id': False,
#                 })
# 
#         for move in too_many:
#             self.write(
#                 cr, uid, [move.id],
#                 {
#                     'product_qty': move.product_qty,
#                     'product_uos_qty': move.product_qty,
#                 })
#             complete.append(move)
# 
#         for move in complete:
#             if prodlot_ids.get(move.id):
#                 self.write(
#                     cr, uid, [move.id],
#                     {'prodlot_id': prodlot_ids.get(move.id)})
#             self.action_done(cr, uid, [move.id], context=context)
#             if move.picking_id.id:
#                 # TOCHECK : Done picking if all moves are done
#                 cr.execute("""
#                     SELECT move.id FROM stock_picking pick
#                     RIGHT JOIN stock_move move ON move.picking_id = pick.id AND move.state = %s
#                     WHERE pick.id = %s""", ('done', move.picking_id.id))
#                 res = cr.fetchall()
#                 if len(res) == len(move.picking_id.move_lines):
#                     picking_obj.action_move(cr, uid, [move.picking_id.id])
#                     wf_service.trg_validate(uid, 'stock.picking', move.picking_id.id, 'button_done', cr)
# 
#         return [move.id for move in complete]
#===============================================================================


class stock_picking(orm.Model):
    _inherit = 'stock.picking'
    
#===============================================================================
#     def _get_valuation_picking_in(self, cr, uid, pick, move, product_price, product_uom,
#                                   product_qty, product_currency, product_avail, context=None):
#         """
#         Valoracion de inventario
#         """
#         context = context or {}
#         move_obj = self.pool.get('stock.move')
#         location_obj = self.pool.get('stock.location')
#         currency_obj = self.pool.get('res.currency')
#         uom_obj = self.pool.get('product.uom')
#         product_obj = self.pool.get('product.product')
#         # <<<< change begin <<<<<<<<<<
#         # get the qty of available Alex
#         product_qty_available = location_obj.get_product_qty_of_checked_locations(
#             cr, uid, [],
#             move.product_id.id, domain=[], context=context, states=['done']).get(
#             move.product_id.id, 0.0)
#         # <<<< change ends <<<<<<<<<<<<
# 
#         # Average price computation
#         if (pick.type == 'in') and (move.product_id.cost_method == 'average'):
#             product = product_obj.browse(cr, uid, move.product_id.id)
#             move_currency_id = move.company_id.currency_id.id
#             context['currency_id'] = move_currency_id
#             qty = uom_obj._compute_qty(cr, uid, product_uom, product_qty, product.uom_id.id)
# 
#             if product.id in product_avail:
#                 product_avail[product.id] += qty
#             else:
#                 # <<< changes begin. we change the way
#                 # of geting available products. Alex
#                 product_avail[product.id] = product_qty_available
# 
#             if qty > 0:
#                 new_price = currency_obj.compute(cr, uid, product_currency,
#                         move_currency_id, product_price)
#                 new_price = uom_obj._compute_price(cr, uid, product_uom, new_price,
#                         product.uom_id.id)
#                 if product_qty_available <= 0:
#                     new_std_price = new_price
#                 else:
#                     # Get the standard price
#                     amount_unit = product.price_get('standard_price', context=context)[product.id]
#                     new_std_price = ((amount_unit * product_avail[product.id])\
#                         + (new_price * qty))/(product_avail[product.id] + qty)
#                 # Write the field according to price type field
#                 product_obj.write(cr, uid, [product.id], {'standard_price': new_std_price})
# 
#                 # Record the values that were chosen in the wizard, so they can be
#                 # used for inventory valuation if real-time valuation is enabled.
#                 move_obj.write(cr, uid, [move.id],
#                         {'price_unit': product_price,
#                          'price_currency_id': product_currency})
#===============================================================================

stock_picking()