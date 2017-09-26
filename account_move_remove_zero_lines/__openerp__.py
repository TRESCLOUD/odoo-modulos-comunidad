{
    'name': 'Account move remove zero lines',
    'version': '1.0',
    'description': """
        This modules creates a funcional one2many field so we can show an account move removing the zero lines so the user is not confused.  This module does NOT affect the actual created move.
    """,
    'author': 'Tim Diamond',
    'website': 'www.altatececuador.com',
    "depends" : [ 'account' ],
    "data" : [ 'account_move_remove_zero_lines.xml' ],
    "installable": True,
    "auto_install": False
}