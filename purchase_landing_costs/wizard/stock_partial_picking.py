# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP s.a. (<http://www.openerp.com>).
#    Copyright (C) 2012-TODAY Mentis d.o.o. (<http://www.mentis.si/openerp>)
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

from osv import osv, fields

class stock_partial_picking(osv.osv_memory):
    _inherit = "stock.partial.picking"

    def _product_cost_for_average_update(self, cr, uid, move):
        """
        Este stock.move que le estamos pasando como parametro devuelve su valor de costo mediante
          el tomar el price_unit_with_costs, para cuando se realiza el ponderado.
        """
        res = super(stock_partial_picking, self)._product_cost_for_average_update(cr, uid, move)
        if move.picking_id.purchase_id and move.purchase_line_id:
            res['cost'] = move.price_unit_with_costs
        return res

    def _partial_move_for(self, cr, uid, move, context=None):
        """
        Si estamos hablando de un stock.picking.in, vamos a actualizar el costo con el valor que tenga
          de precio-con-costos para el nuevo picking parcial. Si no, lo que va a tomar es el costo promedio
          (para productos con metodo de costeo "promedio" ("average")) o normal ("standard").
        """
        result = super(stock_partial_picking, self)._partial_move_for(cr, uid, move, context=context)
        if move.picking_id.purchase_id and move.purchase_line_id:
            pur_currency = move.purchase_line_id.order_id.currency_id.id
            if move.picking_id.allow_landing_costs:
                result.update({
                    'cost': move.price_unit_with_costs
                })
        return result