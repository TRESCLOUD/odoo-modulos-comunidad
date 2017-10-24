# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
import decimal_precision as dp

class bank_acc_rec_statement(osv.osv):
    def check_group(self, cr, uid, ids, context=None):
        """Check if following security constraints are implemented for groups:
        Bank Statement Preparer– they can create, view and delete any of the Bank Statements provided the Bank Statement is not in the DONE state,
        or the Ready for Review state.
        Bank Statement Verifier – they can create, view, edit, and delete any of the Bank Statements information at any time.
        NOTE: DONE Bank Statements  are only allowed to be deleted by a Bank Statement Verifier."""
        model_data_obj = self.pool.get('ir.model.data')
        res_groups_obj = self.pool.get('res.groups')
        group_verifier_id = model_data_obj._get_id(cr, uid, 'npg_bank_account_reconciliation', 'group_bank_stmt_verifier')
        for statement in self.browse(cr, uid, ids, context=context):
            if group_verifier_id:
                res_id = model_data_obj.read(cr, uid, [group_verifier_id], ['res_id'])[0]['res_id']
                group_verifier = res_groups_obj.browse(cr, uid, res_id, context=context)
                group_user_ids = [user.id for user in group_verifier.users]
                if statement.state!='draft' and uid not in group_user_ids:
                    raise osv.except_osv(_('!Error!'),
                                         _('Solamente usuarios que sean miembros del grupo %s pueden editar o eliminar conciliaciones bancarias en estado diferente de borrador.') % group_verifier.name)
        return True  

    def copy(self, cr, uid, id, default={}, context=None):
        default.update({
            'credit_move_line_ids': [],
            'debit_move_line_ids': [],
            'name': '',
        })
        return super(bank_acc_rec_statement, self).copy(cr, uid, id, default=default, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        self.check_group(cr, uid, ids, context) # Check if the user is allowed to perform the action
        return super(bank_acc_rec_statement, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        "Reset the related account.move.line to be re-assigned later to statement."
        statement_line_obj = self.pool.get('bank.acc.rec.statement.line')
        self.check_group(cr, uid, ids, context) # Check if the user is allowed to perform the action
        for statement in self.browse(cr, uid, ids, context=context):
            statement_lines = statement.credit_move_line_ids + statement.debit_move_line_ids
            statement_line_ids = map(lambda x: x.id, statement_lines)
            statement_line_obj.unlink(cr, uid, statement_line_ids, context=context) # call unlink method to reset
        return super(bank_acc_rec_statement, self).unlink(cr, uid, ids, context=context)

    def check_difference_balance(self, cr, uid, ids, context=None):
        "Check if difference balance is zero or not."
        #El siguiente código fue comentado por TRESCLOUD para poder realizar conciliaciones en 0(sin movimientos)
        #for statement in self.browse(cr, uid, ids, context=context):
        #    if statement.difference != 0.0:
        #        raise osv.except_osv(_('!Error!'),
        #                             _(u'No se puede realizar una conciliación bancaria en cero, debe tener al menos un movimiento de débito o crédito seleccionado.'))
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        "Cancel the the statement."
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True

    def action_review(self, cr, uid, ids, context=None):
        "Change the status of statement from 'draft' to 'to_be_reviewed'."
        # If difference balance not zero prevent further processing
        self.check_difference_balance(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'to_be_reviewed'}, context=context)
        return True

    def action_process(self, cr, uid, ids, context=None):
        """Set the account move lines as 'Cleared' and Assign 'Bank Acc Rec Statement ID'
        for the statement lines which are marked as 'Cleared'."""
        
#        self.action_review(cr, uid, ids, context=context)
        
        account_move_line_obj = self.pool.get('account.move.line')
        statement_line_obj = self.pool.get('bank.acc.rec.statement.line')
        statement_line_ids = statement_line_obj.search(cr, uid, [('statement_id', 'in', ids)], context=context)
        for statement_line in statement_line_obj.browse(cr, uid, statement_line_ids, context=context):
            if statement_line.cleared_bank_account:
                if statement_line.move_line_id.bank_acc_rec_statement_id.id != ids[0]:
                    raise osv.except_osv(_(u'¡Error de Usuario!'),
                                         _(u'El registro contable con referencia %s se encuentra asociado a la conciliación %s. Dar click en Actualizar en el estado Borrador')%(statement_line.move_line_id.ref, statement_line.move_line_id.bank_acc_rec_statement_id.name))
        # If difference balance not zero prevent further processing
        self.check_difference_balance(cr, uid, ids, context=context)
        statement_lines_ids = []
        for statement in self.browse(cr, uid, ids, context=context):
            #Se obtienen los id de las lineas debito donde el campo cleared_bank_account es true           
            for debit_move_line in statement.debit_move_line_ids:
                if debit_move_line.cleared_bank_account:
                    statement_lines_ids.append(debit_move_line.id)
            #Se obtienen los id de las lineas credito donde el campo cleared_bank_account es true   
            for credit_move_line in statement.credit_move_line_ids:
                if credit_move_line.cleared_bank_account:
                    statement_lines_ids.append(credit_move_line.id)                    
                    
            for statement_line in statement_line_obj.browse(cr, uid, statement_lines_ids, context=context):
                #Mark the move lines as 'Cleared'mand assign the 'Bank Acc Rec Statement ID'
                if not statement_line.statement_id.id:
                    raise osv.except_osv(_(u'¡Error de Usuario!'),
                                         _(u'Esta conciliación tiene datos incoherentes, envíela a borrador, hago clic en el botón Actualizar y '
                                           u'comience nuevamente el proceso de aprobación, por favor, comunique este error a soporte de Trescloud.'))
                account_move_line_obj.write(cr, uid, [statement_line.move_line_id.id],
                                            {'cleared_bank_account': statement_line.cleared_bank_account,
                                             'bank_acc_rec_statement_id': statement_line.statement_id.id
                                             }, context=context)

            self.write(cr, uid, [statement.id], {'state': 'done',
                                                 'verified_by_user_id': uid,
                                                 'verified_date': time.strftime('%Y-%m-%d')
                                                 }, context=context)
        return True

    def action_cancel_draft(self, cr, uid, ids, context=None):
        """Reset the statement to draft and perform resetting operations."""
        account_move_line_obj = self.pool.get('account.move.line')
        statement_line_obj = self.pool.get('bank.acc.rec.statement.line')
        for statement in self.browse(cr, uid, ids, context=context):
            statement_lines = statement.credit_move_line_ids + statement.debit_move_line_ids
            line_ids = []
            statement_line_ids = []
            for statement_line in statement_lines:
                statement_line_ids.append(statement_line.id)
                if statement_line.move_line_id:
                    line_ids.append(statement_line.move_line_id.id) # Find move lines related to statement lines

            # Reset 'Cleared' and 'Bank Acc Rec Statement ID' to False
            account_move_line_obj.write(cr, uid, line_ids, {'cleared_bank_account': False,
                                                            'bank_acc_rec_statement_id': False,
                                                            }, context=context)
            # Reset 'Cleared' in statement lines
            statement_line_obj.write(cr, uid, statement_line_ids, {'cleared_bank_account': False,
                                                                   'research_required': False
                                                                   }, context=context)
            # Reset statement
            self.write(cr, uid, [statement.id], {'state': 'draft',
                                                 'verified_by_user_id': False,
                                                 'verified_date': False
                                                 }, context=context)

        return True

    def action_select_all(self, cr, uid, ids, context=None):
        """Mark all the statement lines as 'Cleared'."""
        statement_line_obj = self.pool.get('bank.acc.rec.statement.line')
        for statement in self.browse(cr, uid, ids, context=context):
            statement_lines = statement.credit_move_line_ids + statement.debit_move_line_ids
            statement_line_ids = map(lambda x: x.id, statement_lines)
            statement_line_obj.write(cr, uid, statement_line_ids, {'cleared_bank_account': True}, context=context)
        return True

    def action_unselect_all(self, cr, uid, ids, context=None):
        """Reset 'Cleared' in all the statement lines."""
        statement_line_obj = self.pool.get('bank.acc.rec.statement.line')
        for statement in self.browse(cr, uid, ids, context=context):
            statement_lines = statement.credit_move_line_ids + statement.debit_move_line_ids
            statement_line_ids = map(lambda x: x.id, statement_lines)
            statement_line_obj.write(cr, uid, statement_line_ids, {'cleared_bank_account': False}, context=context)
        return True

    def _get_balance(self, cr, uid, ids, name, args, context=None):
        """Computed as following:
        A) Deposits, Credits, and Interest Amount: Total SUM of Amts of lines with Cleared = True
        Deposits, Credits, and Interest # of Items: Total of number of lines with Cleared = True
        B) Checks, Withdrawals, Debits, and Service Charges Amount:
        Checks, Withdrawals, Debits, and Service Charges Amount # of Items:
        Cleared Balance (Total Sum of the Deposit Amount Cleared (A) – Total Sum of Checks Amount Cleared (B))
        Difference= (Ending Balance – Beginning Balance) - cleared balance = should be zero.
"""
        res = {}
        account_precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        for statement in self.browse(cr, uid, ids, context=context):
            res[statement.id] = {
                'sum_of_credits': 0.0,
                'sum_of_debits': 0.0,
                'cleared_balance': 0.0,
                'difference': 0.0,
                'sum_of_credits_lines': 0.0,
                'sum_of_debits_lines': 0.0
            }
            for line in statement.credit_move_line_ids:
                res[statement.id]['sum_of_credits'] += line.cleared_bank_account and round(line.amount, account_precision) or 0.0
                res[statement.id]['sum_of_credits_lines'] += line.cleared_bank_account and 1.0 or 0.0
            for line in statement.debit_move_line_ids:
                res[statement.id]['sum_of_debits'] += line.cleared_bank_account and round(line.amount, account_precision) or 0.0
                res[statement.id]['sum_of_debits_lines'] += line.cleared_bank_account and 1.0 or 0.0

            res[statement.id]['cleared_balance'] = round(res[statement.id]['sum_of_debits'] - res[statement.id]['sum_of_credits'], account_precision)
            res[statement.id]['difference'] = round((statement.ending_balance - statement.starting_balance) - res[statement.id]['cleared_balance'], account_precision)
        return res
    
    def refresh_record(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {}, context=context)
    
    def onchange_account_id(self, cr, uid, ids, account_id, ending_date, suppress_ending_date_filter, context=None):
        account_move_line_obj = self.pool.get('account.move.line')
        statement_line_obj = self.pool.get('bank.acc.rec.statement.line')
        val = {'value': {'credit_move_line_ids': [], 'debit_move_line_ids': []}}
        if account_id:
            for statement in self.browse(cr, uid, ids, context=context):
                statement_line_ids = statement_line_obj.search(cr, uid, [('statement_id', '=', statement.id)], context=context)
                # call unlink method to reset and remove existing statement lines and
                # mark reset field values in related move lines
                #statement_line_obj.unlink(cr, uid, statement_line_ids, context=context)
                if statement_line_ids:
                    cr.execute('''delete from bank_acc_rec_statement_line where id in %s''', (tuple(statement_line_ids),))
                
            # Apply filter on move lines to allow
            #1. credit and debit side journal items in posted state of the selected GL account
            #2. Journal items which are not assigned to previous bank statements
            #3. Date less than or equal to ending date provided the 'Suppress Ending Date Filter' is not checkec
            domain = [('account_id', '=', account_id), ('move_id.state', '=', 'posted'), ('cleared_bank_account', '=', False), ('draft_assigned_to_statement', '=', False), ('date', '<=', ending_date)]
#             if not suppress_ending_date_filter:
#                 domain += [('date', '<=', ending_date)]
            if context.get('start_date'):
                domain += [('date', '>=', context.get('start_date'))]
                
            #Diarios de apertura
            journal_ids = self.pool.get('account.journal').search(cr, uid, [('type','=','situation')], context=context)
            if not context.get('opening_entries'):
                domain += [('journal_id', 'not in', journal_ids)]
               
            line_ids = account_move_line_obj.search(cr, uid, domain, context=context)
            for line in account_move_line_obj.browse(cr, uid, line_ids, context=context):
                res = {
                       'ref': line.ref,
                       'date': line.date,
                       'partner_id': line.partner_id.id,
                       'currency_id': line.currency_id.id,
                       'amount': line.credit or line.debit,
                       'name': line.name,
                       'move_line_id': line.id,
                       'type': line.credit and 'cr' or 'dr'
                }
                if res['type'] == 'cr':
                    val['value']['credit_move_line_ids'].append(res)
                else:
                    val['value']['debit_move_line_ids'].append(res)
        return val

    _name = "bank.acc.rec.statement"
    _columns = {
        'name': fields.char('Name', track_visibility='always', required=True, size=64, states={'done':[('readonly', True)]}, help="This is a unique name identifying the statement (e.g. Bank X January 2012)."),
        'account_id': fields.many2one('account.account', 'Account', track_visibility='always', required=True,
                                                 states={'done':[('readonly', True)]}, domain="[('company_id', '=', company_id), ('type', '!=', 'view')]",
                                                 help="The Bank/Gl Account that is being reconciled."),
        'ending_date': fields.date('Ending Date', track_visibility='always', required=True, states={'done':[('readonly', True)]}, help="The ending date of your bank statement."),
        'starting_balance': fields.float('Starting Balance', track_visibility='always', required=True, digits_compute=dp.get_precision('Account'), help="The Starting Balance on your bank statement.", states={'done':[('readonly', True)]}),
        'ending_balance': fields.float('Ending Balance', track_visibility='always', required=True, digits_compute=dp.get_precision('Account'), help="The Ending Balance on your bank statement.", states={'done':[('readonly', True)]}),
        'company_id': fields.many2one('res.company', 'Company', track_visibility='always', required=True, readonly=True,
                                      help="The Company for which the deposit ticket is made to"),
        'notes': fields.text('Notes', track_visibility='always'),
        'verified_date': fields.date('Verified Date', states={'done':[('readonly', True)]},
                                     track_visibility='always',
                                     help="Date in which Deposit Ticket was verified."),
        'verified_by_user_id': fields.many2one('res.users', 'Verified By', track_visibility='always', states={'done':[('readonly', True)]},
                                      help="Entered automatically by the “last user” who saved it. System generated."),
        'credit_move_line_ids': fields.one2many('bank.acc.rec.statement.line', 'statement_id', 'Credits',
                                                track_visibility='always',
                                                domain=[('type','=','cr')], context={'default_type':'cr'}, states={'done':[('readonly', True)]}),
        'debit_move_line_ids': fields.one2many('bank.acc.rec.statement.line', 'statement_id', 'Debits',
                                               track_visibility='always', domain=[('type','=','dr')], context={'default_type':'dr'}, states={'done':[('readonly', True)]}),
        'cleared_balance': fields.function(_get_balance, method=True, string='Cleared Balance', digits_compute=dp.get_precision('Account'),
                                  type='float', help="Total Sum of the Deposit Amount Cleared – Total Sum of Checks, Withdrawals, Debits, and Service Charges Amount Cleared",
                                  multi="balance"),
        'difference': fields.function(_get_balance, method=True, type='float', string='Difference', digits_compute=dp.get_precision('Account'),
                                       help="(Ending Balance – Beginning Balance) - Cleared Balance.", multi="balance"),
        'sum_of_credits': fields.function(_get_balance, method=True, string='Checks, Withdrawals, Debits, and Service Charges Amount', digits_compute=dp.get_precision('Account'),
                                  type='float', help="Total SUM of Amts of lines with Cleared = True",
                                    multi="balance"),
        'sum_of_debits': fields.function(_get_balance, method=True, type='float', string='Deposits, Credits, and Interest Amount', digits_compute=dp.get_precision('Account'),
                                       help="Total SUM of Amts of lines with Cleared = True",   multi="balance"),
        'sum_of_credits_lines': fields.function(_get_balance, method=True, string='Checks, Withdrawals, Debits, and Service Charges # of Items',
                                  type='float', help="Total of number of lines with Cleared = True",
                                    multi="balance"),
        'sum_of_debits_lines': fields.function(_get_balance, method=True, type='float', string='Deposits, Credits, and Interest # of Items',
                                       help="Total of number of lines with Cleared = True",   multi="balance"),
        'suppress_ending_date_filter': fields.boolean('Remove Ending Date Filter', track_visibility='always', help="If this is checked then the Statement End Date filter on the transactions below will not occur. All transactions would come over."),
        'state': fields.selection([
            ('draft','Draft'),
            ('to_be_reviewed','Ready for Review'),
            ('done','Done'),
            ('cancel', 'Cancel')
            ],'State', select=True, track_visibility='always', readonly=True),
    }
    _inherit = ['mail.thread']
    _defaults = {
        'state': 'draft',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        'ending_date': time.strftime('%Y-%m-%d'),
    }
    _order = "ending_date desc"
    _sql_constraints = [
        ('name_company_uniq', 'unique (name, company_id, account_id)', 'The name of the statement must be unique per company and G/L account!')
    ]
bank_acc_rec_statement()

class bank_acc_rec_statement_line(osv.osv):
    _name = "bank.acc.rec.statement.line"
    _description = "Statement Line"
    _columns = {
        'name': fields.char('Name', size=64, help="Derived from the related Journal Item.", required=True),
        'ref': fields.char('Reference', size=64, help="Derived from related Journal Item."),
        'partner_id': fields.many2one('res.partner', string='Partner', help="Derived from related Journal Item."),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account'),
                               help="Derived from the 'debit' amount from related Journal Item."),
        'date': fields.date('Date', required=True, help="Derived from related Journal Item."),
        'statement_id': fields.many2one('bank.acc.rec.statement', 'Statement', required=True, ondelete='cascade'),
        'move_line_id': fields.many2one('account.move.line', 'Journal Item', help="Related Journal Item."),
        'cleared_bank_account': fields.boolean('Cleared? ', help='Check if the transaction has cleared from the bank'),
        'research_required': fields.boolean('Research Required? ', help='Check if the transaction should be researched by Accounting personal'),
        'currency_id': fields.many2one('res.currency', 'Currency', help="The optional other currency if it is a multi-currency entry."),
        'type':fields.selection([('dr','Debit'),('cr','Credit')], 'Cr/Dr'),
    }

    def create(self, cr, uid, vals, context=None):
        account_move_line_obj = self.pool.get('account.move.line')
        # Prevent manually adding new statement line.
        # This would allow only onchange method to pre-populate statement lines based on the filter rules.
        if not vals.get('move_line_id', False):
            raise osv.except_osv(_('!Error!'),
                                 _(u'No se puede agregar manualmente líneas de débito o crédito en estado listo para revisión.'))
        #Actualizamos el campo draft_assigned_to_statement a true cuando cleared_bank_account es true, las lineas restantes se vuelven a 
        #cargar cuando intenta hacer una nueva conciliacion para esa cuenta
        if vals and 'move_line_id' in vals:
            for statement_line in account_move_line_obj.browse(cr, uid, [vals['move_line_id']], context=context):
                if statement_line.cleared_bank_account:
                    account_move_line_obj.write(cr, uid, [vals['move_line_id']], {'draft_assigned_to_statement': True}, context=context)
        return super(bank_acc_rec_statement_line, self).create(cr, uid, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        """
        Este método actualiza el valor de ciertos campos y se remueven los id con valor False de la lista de ids
        a eliminar
        :param cr: Cursor estándar de base de datos PostgreSQL
        :param uid: ID del usuario actual
        :param ids: IDs de los elementos
        :param context: Diccionario de datos de contexto adicional
        """                
        account_move_line_obj = self.pool.get('account.move.line')
        move_line_ids = [element for element in map(lambda x: x.move_line_id.id, self.browse(cr, uid, ids, context=context)) if element]
        # Reset field values in move lines to be added later
        account_move_line_obj.write(cr, uid, move_line_ids, {
            'draft_assigned_to_statement': False,
            'cleared_bank_account': False,
            'bank_acc_rec_statement_id': False
        }, context=context)
        return super(bank_acc_rec_statement_line, self).unlink(cr, uid, ids, context=context)

bank_acc_rec_statement_line()
