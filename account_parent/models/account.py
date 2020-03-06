# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016 Steigend IT Solutions
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, float_round


class AccountAccountType(models.Model):
    _inherit = "account.account.type"
    
    type = fields.Selection(selection_add=[('view','View')])
    

class AccountAccount(models.Model):
    _inherit = "account.account"

    level =  fields.Integer(string='Level', compute='_get_level', stored=True, help='Account Level')

    @api.one
    @api.depends('parent_id')
    def _get_level(self):
        "Funcion que obtiene el level de la cuenta contable."

        level = 0
        parent = self.parent_id
        while parent:
            level += 1
            parent = parent.parent_id
        self.level = level

    @api.model
    def _move_domain_get(self, domain=None):
        context = dict(self._context or {})
        domain = domain and safe_eval(str(domain)) or []
        date_field = 'date'
        if context.get('aged_balance'):
            date_field = 'date_maturity'
        if context.get('date_to'):
            domain += [(date_field, '<=', context['date_to'])]
        if context.get('date_from'):
            if not context.get('strict_range'):
                domain += ['|', (date_field, '>=', context['date_from']), ('account_id.user_type_id.include_initial_balance', '=', True)]
            elif context.get('initial_bal'):
                domain += [(date_field, '<', context['date_from'])]
            else:
                domain += [(date_field, '>=', context['date_from'])]
        if context.get('journal_ids'):
            domain += [('journal_id', 'in', context['journal_ids'])]
        state = context.get('state')
        if state and state.lower() != 'all':
            domain += [('move_id.state', '=', state)]
        if context.get('company_id'):
            domain += [('company_id', '=', context['company_id'])]
        if 'company_ids' in context:
            domain += [('company_id', 'in', context['company_ids'])]
        if context.get('reconcile_date'):
            domain += ['|', ('reconciled', '=', False), '|', ('matched_debit_ids.create_date', '>', context['reconcile_date']), ('matched_credit_ids.create_date', '>', context['reconcile_date'])]
        return domain


    @api.multi
    @api.depends('move_line_ids','move_line_ids.amount_currency','move_line_ids.debit','move_line_ids.credit')
    def compute_values(self, domain=None):
        default_domain = self._move_domain_get()
        for account in self:
            sub_accounts = self.with_context({'show_parent_account':True, 'not_show_deprecated_account': True}).search([('id','child_of',[account.id])])
            balance = 0.0
            credit = 0.0
            debit = 0.0
            search_domain = default_domain[:]
            search_domain.insert(0,('account_id','in',sub_accounts.ids))
            if domain:
                search_domain += domain
            for aml in self.env['account.move.line'].search(search_domain):
                balance += aml.debit - aml.credit
                credit += aml.credit
                debit += aml.debit
            account.balance = balance
            account.credit = credit
            account.debit = debit

    move_line_ids = fields.One2many('account.move.line','account_id','Journal Entry Lines')
    balance = fields.Float(compute="compute_values", digits=dp.get_precision('Account'), string='Balance')
    credit = fields.Float(compute="compute_values",digits=dp.get_precision('Account'), string='Credit')
    debit = fields.Float(compute="compute_values",digits=dp.get_precision('Account'), string='Debit')
    parent_id = fields.Many2one('account.account','Parent Account',ondelete="set null")
    child_ids = fields.One2many('account.account','parent_id', 'Child Accounts')
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)


    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'code, name'
    _order = 'parent_left'


    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}
        if not context.get('show_parent_account',False):
            args += [('user_type_id.type', '!=', 'view')]
        if context.get('not_show_deprecated_account',False):
            args += [('deprecated', '!=', True)]
        return super(AccountAccount, self).search(args, offset, limit, order, count=count)

    @api.model
    def _get_parent(self, all_parents=False):
        "Funcion para obtener padres de cuenta contables."
        res = None
        parents = self.with_context({'show_parent_account': True, 'not_show_deprecated_account': True}).search([('child_ids', 'in', self.id), ('code', '!=', '0.'), ('code', '!=', '0')], order='code ASC')
        if parents:
            res = parents[0]._get_array_parent(all_parents)
        return res

    @api.model
    def _get_array_parent(self, all_parents=False):
        "Funcion para obtener Arreglo de cuentas padres"
        res = self
        parents = self.with_context({'show_parent_account': True, 'not_show_deprecated_account': True}).search([('child_ids', 'in', self.id), ('code', '!=', '0.'), ('code', '!=', '0')], order='code ASC')
        if parents:
            for parent in parents:
                if all_parents:
                    res += parent._get_array_parent(all_parents)
                else:
                    res = parent._get_array_parent(all_parents)
        return res

    @api.model
    def _get_principal_children_by_order(self, **kwargs):
        "Funcion para obtener hijos de cuenta contables."
        res = None
        children = self.with_context({'show_parent_account': True, 'not_show_deprecated_account': True}, **kwargs).search([('parent_id', 'in', self._ids)], order='code ASC')
        if children:
            for child in children:
                if res:
                    res += child._get_children_by_order()
                else:
                    res = child._get_children_by_order()
        return res

    @api.model
    def _get_children_by_order(self, **kwargs):
        res = self
        children = self.with_context({'show_parent_account': True, 'not_show_deprecated_account': True }, **kwargs).search([('parent_id', 'in', self.ids)], order='code ASC')
        if children:
            for child in children:
                res += child._get_children_by_order()
        return res

    @api.model
    def _get_balance_account(self, where=None):
        "Funcion para obtener sumatoria de Debitos y Creditos de cuenta contables."
        sql = "select COALESCE(SUM(debit),0) AS debit, COALESCE(SUM(credit),0) AS credit " \
              "from account_move am " \
              "JOIN account_move_line l on am.id=l.move_id " \
              "JOIN account_account acc ON l.account_id = acc.id " \
              "JOIN account_account_type acct ON acc.user_type_id = acct.id " \
              "where l.account_id = "+str(self.id)
        if where:
            sql += where
        self.env.cr.execute(sql)
        res = self.env.cr.dictfetchone()
        return res.get('debit') or 0.0, res.get('credit') or 0.0

    @api.multi
    def _get_max_level(self):
        "Funcion para obtener el Level mas alto de todas las cuentas contables."
        search_ids = self.env['account.account'].search([])
        max_id = search_ids and max(search_ids, key=lambda item: item.level)
        if max_id:
            return max_id.level or 0
        return 0

    def _get_set_accounts_data(self, accounts, where, all_accounts=False):
        "Metodo que recorre un arreglo de cuentas contables, crea un arbol con el saldo debito, credito y balance de dicho arbol contable."
        class VirtualData():
            def __init__(self, account_id, debit=0.0, credit=0.0):
                self.account_id = account_id
                self.debit = debit
                self.credit = credit
                self.balance = debit - credit
        res = []
        parent_accounts = []
        prec = self.env['decimal.precision'].precision_get('Account')
        for account in accounts:
            acc = account._get_parent(not all_accounts)
            if acc:
                parent_accounts += acc
            set_accounts = set(parent_accounts)
            parent_accounts = list(set_accounts)
        for accountp in sorted(parent_accounts, key=lambda aux: aux.code):
            accounts = accountp._get_children_by_order()
            for account in sorted(accounts, key=lambda aux: aux.code, reverse=True):
                childrens = account._get_principal_children_by_order()
                debit = 0
                credit = 0
                if account.level == self._get_max_level() or not childrens:
                    debit, credit = account._get_balance_account(where)
                else:
                    for record in res:
                        if record.account_id.parent_id.id == account.id:
                            debit += record.debit
                            credit += record.credit
                debit = float_round(debit, precision_digits=prec)
                credit = float_round(credit, precision_digits=prec)
                res += [VirtualData(account, debit, credit)]
        res_aux = []
        for aux in sorted(res, key=lambda account: account.account_id.code):
            res_aux += [aux]
        return res_aux

    
class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    @api.model
    def _prepare_liquidity_account(self, name, company, currency_id, type):
        res = super(AccountJournal, self)._prepare_liquidity_account(name, company, currency_id, type)
        # Seek the next available number for the account code
        code_digits = company.accounts_code_digits or 0
        if type == 'bank':
            account_code_prefix = company.bank_account_code_prefix or ''
        else:
            account_code_prefix = company.cash_account_code_prefix or company.bank_account_code_prefix or ''

        liquidity_type = self.env.ref('account_parent.data_account_type_view')
        parent_id = self.env['account.account'].search([('code','=',account_code_prefix),
                                                        ('company_id','=',company.id),('user_type_id','=',liquidity_type.id)], limit=1)
        
        if parent_id:
            res.update({'parent_id':parent_id.id})
        return res

