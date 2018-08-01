# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville.
#    Copyright 2015 Camptocamp SA
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
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _

class AccountMove(osv.osv):
    _inherit = 'account.move'

    _columns = {
        'locked': fields.boolean('Locked')
    }

    def write(self, cr, user, ids, vals, context=None):
        context = context and context or {}
        for move in self.browse(cr, user, ids):
            if move.locked and not context.get('allow_unlock', False):
                raise osv.except_osv(_('Error!'), _(
                    'Move locked'))
        return super(AccountMove, self).write(cr, user, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        context = context and context or {}
        for move in self.browse(cr, uid, ids):
            if move.locked and not context.get('allow_unlock', False):
                raise osv.except_osv(_('Error!'), _(
                    'Move locked'))
        return super(AccountMove, self).unlink(cr, uid, ids)

    def button_cancel(self, cr, uid, ids, context=None):
        # Cancel a move was done directly in SQL
        # so we need to test manualy if the move is locked
        context = context and context or {}
        for move in self.browse(cr, uid, ids):
            if move.locked and not context.get('allow_unlock', False):
                raise osv.except_osv(_('Error!'), _(
                    'Move locked'))
        return super(AccountMove, self).button_cancel(cr, uid, ids, context=None)

AccountMove()
