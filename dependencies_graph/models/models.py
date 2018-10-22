# -*- coding: utf-8 -*-

from odoo import models, fields, api


class dependencies_graph_settings(models.Model):
    _name = 'dependencies_graph.settings'

    module_ids = fields.Many2many('ir.module.module', 'dependencies_graph_module_dependency', 'settings_id',
                                  'module_id')
