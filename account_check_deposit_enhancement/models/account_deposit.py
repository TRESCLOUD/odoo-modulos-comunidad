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
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_compare


class account_check_deposit(orm.Model):
    _inherit = "account.check.deposit"
    
    def _new_domain(self, cr, uid, ids, fields, args=None, context=None):
        """
        Campo funcional interno que no se guarda. Nos sirve para mantener el 
        dominio de los diarios que realizan pagos con cheques, segun la
        configuracion de los mismos
        :param cr: Cursor estándar de base de datos PostgreSQL
        :param uid: ID del usuario actual.
        :param ids: IDs de los objetos a los cuales calcular este campo.
        :param field: Campo siendo evaluado (no se usa).
        :param args: Argumentos adicionales (no se usa).
        :param context: Datos adicionales de contexto.
        :return: Mapeo id => booleano.
        """
        if context is None:
            context = {}
        res = {}
        for id in ids:
            res[id] = self.default_get(cr, uid, fields, context=context).get('new_domain')
        return res
    
    def default_get(self, cr, user, fields, context=None):
        """
        Le adjunta, a los defaults calculados, el calculo del campo new_domain.
        :param cr: Cursor estándar de base de datos PostgreSQL
        :param user: ID del usuario actual.
        :param fields: Lista de campos a tratar.
        :param context: Datos adicionales de contexto.
        :return: Diccionario de valores predeterminados.
        """
        if context is None:
            context = {}
        res = super(account_check_deposit, self).default_get(cr, user, fields, context=context)
        journal_ids = self.pool.get('account.journal').search(cr, user, 
                                  [('control_customer_check','=',True)])
        # Busca todos los voucher de los diarios que son de tipo clientes
        # devuelve los ids de los pagos, realizados en estos diarios. 
        cr.execute("select aj.id from account_voucher as av join account_journal as aj \
                    on av.journal_id = aj.id where av.state_check_control = 'received_check' \
                    and aj.id in %s",(tuple(journal_ids),))
        ids = [id[0] for id in cr.fetchall()]
        res.update({
            'new_domain': ids
        })
        return res
    
    def _compute_check_deposit(self, cr, uid, ids, name, args, context=None):
        '''
        Metodo que devuelve campos calculados como el numero de cheques
        en el deposito, el total del deposito, si la moneda en la que estamos
        depositando es la misma que la de la compania y si el deposito esta
        conciliado. 
        '''
        res = {}
        for deposit in self.browse(cr, uid, ids, context=context):
            total = 0.0
            count = 0
            reconcile = False
            currency_none_same_company_id = False
            if deposit.company_id.currency_id != deposit.currency_id:
                currency_none_same_company_id = deposit.currency_id.id
            for line in deposit.check_payment_ids:
                count += 1
                if currency_none_same_company_id:
                    total += line.amount_currency
                else:
                    total += line.amount
            if deposit.move_id:
                for line in deposit.move_id.line_id:
                    if line.debit > 0 and line.reconcile_id:
                        reconcile = True
            res[deposit.id] = {
                'total_amount': total,
                'is_reconcile': reconcile,
                'currency_none_same_company_id': currency_none_same_company_id,
                'check_count': count,
                }
        return res
    
    def validate_deposit(self, cr, uid, ids, context=None):
        '''
        Valida el deposito, Cambia de estado el pago a cheques depositados.
        :param ids: Ids del deposito
        :param context: Variables de contexto o de ambiente
        '''
        context = context or {}
        am_obj = self.pool['account.move']
        aml_obj = self.pool['account.move.line']
        av_obj = self.pool.get('account.voucher')
        line_ids = []
        # Se configura la nueva logica para voucher.
        for deposit in self.browse(cr, uid, ids, context=context):
            move_vals = self._prepare_account_move_vals(
                cr, uid, deposit, context=context)
            context['journal_id'] = move_vals['journal_id']
            context['period_id'] = move_vals['period_id']
            move_id = am_obj.create(cr, uid, move_vals, context=context)
            total_debit = 0.0
            total_amount_currency = 0.0
            to_reconcile_line_ids = []
            for voucher in deposit.check_payment_ids:
                line_ids.append(voucher.id) 
                move_voucher = voucher.move_id
                line = [line for line in move_voucher.line_id  
                        if float_compare(line.debit, voucher.amount, precision_digits=2) == 0 \
                        and voucher.account_id.id == line.account_id.id]
                total_debit += line and line[0].debit or 0.0
                total_amount_currency += line and line[0].amount_currency or 0.0
                line_vals = self._prepare_move_line_vals(
                    cr, uid, line and line[0] or False, context=context)
                line_vals['move_id'] = move_id
                line_vals['name'] += _(' - Check Number: %s') % voucher.check_number
                move_line_id = aml_obj.create(
                    cr, uid, line_vals, context=context)
                to_reconcile_line_ids.append([line and line[0].id or False, move_line_id])
            counter_vals = self._prepare_counterpart_move_lines_vals(
                cr, uid, deposit, total_debit, total_amount_currency,
                context=context)
            counter_vals['move_id'] = move_id
            counter_vals['account_id'] = deposit.account_id.id
            aml_obj.create(cr, uid, counter_vals, context=context)
            am_obj.post(cr, uid, [move_id], context=context)
            deposit.write({'state': 'done', 'move_id': move_id})
            # We have to reconcile after post()
            for reconcile_line_ids in to_reconcile_line_ids:
                aml_obj.reconcile(
                    cr, uid, reconcile_line_ids, context=context)
            av_obj.write(cr, uid, line_ids, {'state_check_control': 'deposited_check'})
        return True
    
    def onchange_journal_id(self, cr, uid, ids, journal_id, context=None):
        '''
        Si se cambia el diario entonces se debe cambiar la cuenta contable,
        y si esta enlazada con una cuenta bancaria, esta sera seteada en este cambio.
        :param journal_id: Id del diario a analizar
        :param context: Variables de contexto o de ambiente
        '''
        context = context or {}
        res = super(account_check_deposit, self).onchange_journal_id(cr, uid, ids, journal_id, context=context)
        values = {'value':{}}
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
            partner_bank_ids = [partner_bank_id.id for partner_bank_id in journal.partner_bank_ids]
            values['value'].update(partner_bank_id=partner_bank_ids and \
                                   partner_bank_ids[0] or False, account_id= \
                                   journal.default_debit_account_id.id)
        else:
            values['value'].update(partner_bank_id=False,account_id=False)
        return values 
    
    _columns = {
        'account_id': fields.many2one('account.account', 'Account'),
        'check_payment_ids': fields.one2many('account.voucher', 
                                             'check_deposit_id', 'Check Payments',
                                             states={'done': [('readonly', '=', True)]}),
        'new_domain': fields.function(_new_domain, type='char', 
                                      method=True, store=False,
                                      string='Domain'),
        'currency_none_same_company_id': fields.function(
            _compute_check_deposit, type='many2one',
            relation='res.currency', multi='deposit',
            string='Currency (False if same as company)'),
        'total_amount': fields.function(
            _compute_check_deposit, multi='deposit',
            string="Total Amount", readonly=True,
            type="float", digits_compute=dp.get_precision('Account')),
        'check_count': fields.function(
            _compute_check_deposit, multi='deposit', readonly=True,
            string="Number of Checks", type="integer"),
        'is_reconcile': fields.function(
            _compute_check_deposit, multi='deposit', readonly=True,
            string="Reconcile", type="boolean"),
                }
    

account_check_deposit()