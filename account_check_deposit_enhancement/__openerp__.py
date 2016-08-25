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

{
    'name': 'Account Check Deposit Enhancement',
    'version': '0.1',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Manage deposit of checks to the bank',
    'description': """
Account Check Deposit
=====================
This module allows you to easily manage check deposits : you can select all
the checks you received as payments and create a global deposit for the
selected checks.

A journal for received checks is automatically created.
You must configure on this journal the default debit account and the default
credit account. You must also configure on the company the account for
check deposits.
""",
    'author': "TRESCloud",
    'website': 'http://www.trescloud.com/',
    'depends': [
                'base',
                'account',
                'account_check_deposit',
                'ecua_check',
    ],
    'data': [
             'data/account_account_data.xml',
             'data/account_journal_data.xml',
             'data/locked_objects.xml',
             'views/account_voucher_view.xml',
             'views/account_journal_view.xml',
             'views/account_deposit_view.xml',
             'wizard/account_check_receive_view.xml',
             'wizard/account_check_reject_view.xml',
             'wizard/account_check_delay_view.xml',
    ],
    'installable': True,
    'application': True,
}
