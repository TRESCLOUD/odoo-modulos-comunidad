# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class CrmTeam(models.Model):
    _inherit = "crm.team"
    
    @api.model
    def _auto_init(self):
        '''
        Elimina el equipo de venta "Ventas Directas"
        '''
        res = super(CrmTeam, self)._auto_init()
        if self.env['crm.team'].search([
            ('name', '=', 'Direct Sales')]):
            self.env.cr.execute('''
                DELETE FROM crm_team WHERE name = 'Direct Sales';'''
            )
        return res