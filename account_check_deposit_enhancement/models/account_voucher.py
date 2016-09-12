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


class account_voucher(osv.osv):
    _inherit = 'account.voucher'

    _STATES_CHECKS = [
        ('got_check','Cheques Receptados Caja'),
        ('received_check','Cheques Recibido'),
        ('deposited_check','Cheques Depositado'),
        ('rejected_check','Cheques Protestado'),
        ('delayed_check','Cheques Detenidos')
    ]
    
        
    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None):
        '''
        Invocamos el método onchange_partner_id para resetear los campos de cheque en caso que cambie el partner
        :param cr: Cursor estándar de base de datos PostgreSQL
        :param uid: ID del usuario actual
        :param ids: IDs del pago
        :param partner_id: Partner
        :param journal_id: Diario
        :param amount: Importe
        :param currency_id: Moneda
        :param ttype: Tipo de pago
        :param date: Fecha
        :param context: Diccionario de contexto adicional
        '''
        if context is None:
            context = {}         
        vals = super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=context)
        if ttype == 'receipt':
            vals['value'].update({
                'bank_account_partner_id': False,
                'check_number': '',
                'deposit_date': False
            })
        return vals
    
    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        '''
        Al Cambio diario nos indicara si la forma de pago es por manejo, de cheques o es un pago con otros diarios
        :param journal_id: Diario de pago
        :param line_ids: Lineas de deudas de facturas
        :param tax_id: Impuestos
        :param partner_id: Empresa del pago
        :param date: Fecha del pago
        :param amount: Monto del pago
        :param ttype: Tipo de pago,(cliente o proveedor)
        :param company_id: Compania del pago
        :param context: Variables de contexto o de ambientes
        '''
        if not context:
            context = {}            
        vals = super(account_voucher, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=context)
        if vals and vals.get('value',False):
            journal_obj = self.pool.get('account.journal')
            journal = None
            allow_control_check = False
            if journal_id:
                # Si existe un diario en el pago entonces se verifica si tiene control de cheques
                journal = journal_obj.browse(cr, uid, journal_id, context=context)
                allow_control_check = journal.control_customer_check
                if allow_control_check and vals['value'].get('check_number'):
                    res['value'].pop('check_number')
            if ttype == 'receipt':
                # Se aplica solo a pagos desde clientes
                vals['value'].update({
                    'bank_account_partner_id': False,
                    'check_number': '',
                    'deposit_date': False,
                    'check_manage': allow_control_check
                })
        return vals
    
    def _get_invoice(self, cr, uid, ids, name, args, context=None):
        '''
        Metodo que devuelve las facturas del voucher y al deposito de cheque que pertenece
        :param ids: Pagos a analizar
        :param name: Variable no usada necesaria del campo funcional
        :param args: Variable no usada necesaria del campo funcional
        :param context: Variables de contexto
        '''
        if context is None:
            context = {}
        # Inicializacion del dict de valores
        res = dict.fromkeys(ids, {'invoice_payed': '', 'check_deposit_id': False})
        for voucher_id in self.browse(cr, uid, ids, context=context):
            if voucher_id.move_id:
                # Del movimiento contable: si ya esta en una deposito
                # Entonces debes estar en la concilicion de una de las
                # lineas de asiento contable del pago
                for move_line in voucher_id.move_id.line_id:
                    if move_line.check_deposit_id:
                        res[voucher_id.id]['check_deposit_id'] = move_line.check_deposit_id.id
            for line in voucher_id.line_cr_ids:
                # Buscamos a que factura corresponde el pago que se esta realizando.
                if line.move_line_id:
                    if line.move_line_id.invoice:
                        res[voucher_id.id]['invoice_payed'] += line.move_line_id.invoice.internal_number or '' +'\n'
                        continue
        return res
    
    _columns = {
        'check_manage': fields.boolean('Check manage', help='Payment with check management'),
        'bank_account_partner_id': fields.many2one('res.partner.bank', 'Number account', help='Bank Account Number of the customer.',
                                                   track_visibility='always'),
        'check_deposit_id': fields.function(_get_invoice, relation='account.check.deposit', store=True,
                                            type='many2one', multi='calc', string='Check Deposit', 
                                            readonly=True, help='Deposit Check that belongs the voucher'),
        'deposit_date': fields.date('Deposit Date', 
                                    track_visibility='always',
                                    help='Date on which the check will be deposited according to the negotiation with the customer.'),
        'new_deposit_date': fields.date('Deposit Date', 
                                        help='New deposit date of the check, used when the deposit is delayed',
                                        track_visibility='always'),
        'state_check_control': fields.selection(_STATES_CHECKS, 'State control checks', 
                                                help='It used to show what state of the process is the check',
                                                track_visibility='always',),
        'rejected_reason': fields.char('Rejected reason', help='Reason for what the check was rejected'),
        'invoice_payed': fields.function(_get_invoice, method=True, type='char', 
                                         multi='calc', string='Payed Invoices',
                                         help='This field is to make a list of invoices that are paid by this method'),
    }
    
    _defaults = {
        'state_check_control': 'got_check',
        'deposit_date': fields.date.context_today,
    }

account_voucher()