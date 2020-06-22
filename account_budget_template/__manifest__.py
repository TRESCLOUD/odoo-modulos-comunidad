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

{
    "name": "Budget Template",
    "version": "10.0.1",
    "depends": ["account_budget"],
    "author": "Aurium Technologies",
    "category": "Accounting",
    "description": """
   This is a module for creating budgets from templates
    """,
    'demo': [],
    'data': [
        'views/budget.xml',
        'wizard/select_template.xml',
    ],
    'qweb': [
    ],
    'images': ['static/description/banner.png',],
    'installable': True,
    'application': True,
    'auto_install': False,
}
