# -*- coding: utf-8 -*-
{
    'name': "Dependencies Graph",

    'summary': """
        Visualize the dependencies graph for Odoo modules and JavaScript services""",

    # 'description': """
    #     Long description of module's purpose
    # """,

    'author': "Adrian Chang",
    'application': True,
    # 'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Technical Settings',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/resources.xml',
    ],
    # # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
