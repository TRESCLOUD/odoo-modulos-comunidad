# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'CRM Claim Management',
    'version': '1.0',
    'category': 'Sales',
    'sequence': 5,
    'license':'OPL-1',
    'author': "BrowseInfo",
    'website': 'www.browseinfo.in',
    'summary': 'This plugin helps to manage after sales services as claim management',
    'description': "Claim system for your product, claim management, submit claim, claim form, Ticket claim, support ticket, issue, website project issue, crm management, ticket handling,support management, project support, crm support, online support management, online claim, claim product, claim services, issue claim, fix claim, raise ticket, raise issue, view claim, display claim, list claim on website ",
    'depends': [
        'crm',
        'sale',
        'sales_team',
    ],
    'data': [
        #Security
        'security/bi_crm_claim_security.xml',
        'security/ir.model.access.csv',
        #Views
        'views/crm_claim_menu.xml',
        'views/crm_claim_data.xml',
        'views/res_partner_view.xml',
        #TO-DO: ANALIZAR SI SE ELIMINA DEFINITIVAMENTE ESTE ARCHIVO.
        #El codigo se encuentra en 'crm_claim_menu.xml' con adiciones y modificaciones.
        #'views/crm_claim_view.xml',
    ],
    #'demo': ['demo/crm_claim_demo.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
    "images":['static/description/Banner.png'],
}
