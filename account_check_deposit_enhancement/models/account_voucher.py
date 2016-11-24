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
    
    def copy(self, cr, uid, voucher_id, default=None, context=None):
        '''
        Invocamos el metodo copy para setear a false algunos campos
        :param cr: Cursor estándar de base de datos de PostgreSQL
        :param uid: ID del usuario actual
        :param voucher_id: ID del pago
        :param default: Diccionario con valores por defecto
        :param context: Diccionario de contexto adicional
        '''
        if default is None:
            default = {}
        if context is None:
            context = {}
        default.update({'entry_date_rejected': False, 'date_rejected': False, 'rejected_move_id': False})
        return super(account_voucher, self).copy(cr, uid, voucher_id, default=default, context=context)
    
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
    
    def action_protesting_check(self, cr, uid, ids, context=None):
        '''
        Este método levanta un wizard para protestar los cheques
        :param cr: Cursor estándar de base de datos de PostgreSQL
        :param uid: ID del usuario actual
        :param ids: IDs del voucher
        :param context: Diccionario de contexto adicional
        '''
        if context is None:
            context = {}
        obj, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_check_deposit_enhancement', 'view_rejected_check_form')
        return {
            'name': 'Protestar Cheque',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id or False,
            'res_model': 'wizard.rejected.check',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new'
        }
        
    def proforma_voucher(self, cr, uid, ids, context=None):
        for voucher_id in self.browse(cr, uid, ids, context=context):
            if voucher_id.check_manage:
                voucher_ids = self.search(cr, uid, [('check_number','=',voucher_id.check_number), 
                                                    ('journal_id','=',voucher_id.journal_id.id),
                                                    ('partner_id','=',voucher_id.partner_id.id),
                                                    ('id','!=',voucher_id.id),('state','!=','draft')], 
                                          context=context)
                if voucher_ids:
                    raise osv.except_osv(_('Error!'), _('El cheque que esta intentando ingresar, ya fue registrado en el sistema!!!\n ' 
                                                        'Por favor verifique la informacion ingresada'))
        return super(account_voucher, self).proforma_voucher(cr, uid, ids, context=context)
    
    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, type_, date, context=None):
        """
        Borramos la cuenta bancaria del partner asociado.
        :param cr: Cursor estándar de base de datos PostgreSQL
        :param uid: ID del usuario actual
        :param ids: IDs de los elementos a los cuales procesar el cambio.
        :param partner_id: Nuevo valor
        :param journal_id: Nuevo valor
        :param amount: Nuevo valor
        :param currency_id: Nuevo valor
        :param type_: Nuevo valor del campo type
        :param date: Nuevo valor
        :param context: Datos adicionales de contexto.
        :return:
        """
        res = super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount,
                                                               currency_id, type_, date, context)
        res['value'].update({'bank_account_partner_id': False})
        return res
    
    def show_accounting_entries(self, cr, uid, ids, context=None):
        '''
        Muestra los apuntes contables relacionados con el pago
        :param cr: Cursor estándar de base de datos de PostgreSQL
        :param uid: ID del usuario actual
        :param ids: IDs del voucher
        :param context: Diccionario de datos de contexto adicional
        '''
        if context is None:
            context = {}
        accounting_entries_ids = []
        model_data_obj = self.pool.get('ir.model.data')        
        result = model_data_obj.get_object_reference(cr, uid, 'account', 'action_move_journal_line')
        id = result and result[1] or False
        result = self.pool.get('ir.actions.act_window').read(cr, uid, [id], context=context)[0]
        voucher = self.browse(cr, uid, ids[0], context=context)
        for move in voucher.move_ids:
            if move.move_id.id not in accounting_entries_ids:
                accounting_entries_ids.append(move.move_id.id)
        if voucher.rejected_move_id:
            accounting_entries_ids.append(voucher.rejected_move_id.id)
        if len(accounting_entries_ids) > 1:
            result['domain'] = "[('id','in',["+','.join(map(str, accounting_entries_ids))+"])]"
        else:
            res = model_data_obj.get_object_reference(cr, uid, 'account', 'view_move_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = accounting_entries_ids and accounting_entries_ids[0] or False
        return result
    
    _columns = {
        'check_deposit_id': fields.many2one('account.check.deposit',
                                            'Check Deposit'),
        'deposit_date': fields.date('Deposit Date', 
                                    track_visibility='onchange',
                                    help="Date on which the check will be deposited according to the negotiation with the customer."),
        'new_deposit_date': fields.date('Deposit Date', track_visibility='onchange',
                                        help="New deposit date of the check, used when the deposit is delayed"),
        'state_check_control': fields.selection(_STATES_CHECKS, 'State control checks', track_visibility='onchange',
                                                help="It used to show what state of the process is the check"),
        'rejected_reason': fields.char('Rejected reason', help="Reason for what the check was rejected"),
        'invoice_payed': fields.function(_get_invoice, method=True, type='char', 
                                         multi='calc', string='Payed Invoices',
                                         help="This field is to make a list of invoices that are paid by this method"),
        'entry_date_rejected': fields.date('Document Date', 
                                           help='The date of the document support if any (eg complaint to deregister a stolen good)'),
        'date_rejected': fields.date('Accounting Date', 
                                     help='The date of involvement based accounting which affects the balance of the company'),
        'rejected_move_id': fields.many2one('account.move', 'Accounting Entries Rejected Check', 
                                            help='This field defines the accounting entry related to the check protested'),
        'bank_account_partner_id': fields.many2one('res.partner.bank', 'Number account', 
                                                   help="Bank Account Number of the customer.",
                                                   track_visibility='onchange'),
    }
    
    _defaults = {
        'state_check_control': 'got_check',
        'deposit_date': fields.date.context_today,
    }
    
    def onchange_journal(self, cr, uid, ids, journal_id, line_ids,
                         tax_id, partner_id, date, amount, ttype,
                         company_id, context=None):
        '''
        Al Cambio diario nos indicara si la forma de pago es por manejo,
        de cheques o es un pago con otros diarios
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
        default = super(account_voucher, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=context)
        if default and default.get('value',False):
            journal_obj = self.pool.get('account.journal')
            journal = None
            allow_control_check = False
            if journal_id:
                # Si existe un diario en el pago entonces se verifica si tiene control de cheques
                journal = journal_obj.browse(cr, uid, journal_id, context=context)
                allow_control_check = journal.control_customer_check
                if allow_control_check and default['value'].get('check_number'):
                    res['value'].pop('check_number')
            if ttype == 'receipt':
                # Se aplica solo a pagos desde clientes
                default['value'].update({'check_manage': allow_control_check})
        return default

account_voucher()
