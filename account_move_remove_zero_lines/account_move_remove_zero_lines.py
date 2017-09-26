# -*- coding: utf-8 -*-
#################################################################################
#
# A module that contains a credit card model can be attached to other
# objects (e.g. invoices).
#
# Author:  Tim Diamond
# Company: AltaTec Ecuador
# Date:    Jan. 17th, 2014
#
#################################################################################
from openerp.osv import fields, osv, orm


#####################################################################################
# Class definition for credit_card
#####################################################################################
class account_move_lines_no_zeros( osv.osv_memory ):

    _name = "account.move.lines.no.zeros"

    #####################################################################################
    # Column definition
    #####################################################################################
    _columns = { 
                'partner_id':fields.many2one('res.partner', string='Empresa'),
                'account_id':fields.many2one('account.account', string="Cuenta"),
                'product_id':fields.many2one('product.product', string="Producto"),
                'debit':fields.float(string="Debe"),
                'credit':fields.float(string="Haber"),
                'account_invoice_id':fields.many2one('account.invoice'),
               }
    
class account_invoice( orm.Model ):
    _inherit = 'account.invoice'
    
    def get_no_zero_lines(self, cr, uid, ids, field_name, arg, context):
        res = {}
        no_zero_obj = self.pool.get("account.move.lines.no.zeros")
        for r in self.browse(cr,uid,ids):
            res[r.id] = []
            if r.move_id.line_id:
                for line in r.move_id.line_id:
                    if(abs(line.debit) >= .00001):
                        new_line_id = no_zero_obj.create(cr,uid, 
                                           {'partner_id':line.partner_id.id if line.partner_id else None,
                                            'account_id': line.account_id.id if line.account_id else None,
                                            'product_id': line.product_id.id if line.product_id else None,
                                            'debit': line.debit,
                                            'credit': line.credit,
                                            'account_invoice_id': r.id,
                                            }, context=context)
                        res[r.id].append(new_line_id)
                for line in r.move_id.line_id:
                    if(abs(line.credit) >=.00001):
                        new_line_id = no_zero_obj.create(cr,uid, 
                                           {'partner_id':line.partner_id.id if line.partner_id else None,
                                            'account_id': line.account_id.id if line.account_id else None,
                                            'product_id': line.product_id.id if line.product_id else None,
                                            'debit': line.debit,
                                            'credit': line.credit,
                                            'account_invoice_id': r.id,
                                            }, context=context)
                        res[r.id].append(new_line_id)          
        return res
                
    
    _columns = {
                'shadow_move':fields.function(get_no_zero_lines, type='one2many', obj='account.move.lines.no.zeros', string='Asiento', method=True),
                }



