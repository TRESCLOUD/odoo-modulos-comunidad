# -*- coding: utf-8 -*-
##############################################################################
#
#    Aurium Technologies,  Morocco
#    Copyright (C) UNamur <http://www.auriumtechnologies.com>
#    Author: Jalal ZAHID (<https://www.auriumtechnologies.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, _

class AccountBudget(models.Model):

    _inherit = 'crossovered.budget'
    template = fields.Many2one(comodel_name='budget.template', string='Budget template', readonly=True)


class BudgetTamplate(models.Model):
    _name = 'budget.template'

    name = fields.Char(string='Name', size=128, required=True)
    template_lines_ids = fields.One2many(string="Template Lines", comodel_name="budget.template.line", inverse_name="template_id")


class BudgetTemplateLine(models.Model):
    _name = 'budget.template.line'

    name = fields.Char(string='Name')
    template_id = fields.Many2one('budget.template', string='Budget Template')
    budget_position = fields.Many2one('account.budget.post', string='Budget Position', required=True)
    amount = fields.Float('Planned amount', required=True, default=0.0)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analyitc account')