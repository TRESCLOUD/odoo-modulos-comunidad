# -*- coding: utf-8 -*-
import json
import xml.etree.ElementTree as ET

import odoo
from odoo import http
import odoo.modules.graph


class DependenciesGraph(http.Controller):

    @http.route('/dependencies_graph/graph/', auth='user')
    def index(self, **kw):
        scripts = []
        modules = http.request.env.ref('dependencies_graph.basic_settings').module_ids.mapped('name')

        if modules:
            cr = http.request.cr
            query = """SELECT arch_db
                         FROM ir_ui_view v
                    LEFT JOIN ir_model_data md ON (md.model = 'ir.ui.view' AND md.res_id = v.id)"""
            cr.execute(query + 'WHERE md.module IN %s', (tuple(modules),))
            views = cr.fetchall()

            for (view,) in views:
                # Modificado por TRESCLOUD: da problemas por codificacion ASCII
                #root = ET.fromstring(view)
                root = ET.fromstring(view.encode('utf-8'))
                #
                for script in root.iter('script'):
                    if 'src' in script.attrib:
                        scripts.append(script.attrib['src'])
            scripts = list(set(scripts))

        return http.request.render('dependencies_graph.graph', {'scripts': scripts})

    @http.route('/dependencies_graph/modules', type='json', auth='user')
    def get_graph(self):
        cr = http.request.cr
        graph = odoo.modules.graph.Graph()

        cr.execute("SELECT name, state FROM ir_module_module")
        graph.add_modules(cr, map(lambda m: m[0], cr.fetchall()))

        response = {}
        for key, value in graph.iteritems():
            response[key] = {}
            response[key]['depends'] = value.info['depends']
            response[key]['name'] = value.info['name']
            response[key]['state'] = value.state

        return json.dumps(response)

    @http.route('/dependencies_graph/models', type='json', auth='user')
    def get_models(self):
        cr = http.request.cr

        cr.execute("""SELECT model, model_id, name, field_description, ttype, relation, 
                                    relation_field, readonly, required,
                                    relation_table, column1, column2
                      FROM ir_model_fields""")
        models = cr.fetchall()
        response = {}
        for model in models:
            model_name, model_id, name, field_description, ttype, relation, relation_field, readonly, required, relation_table, column1, column2 = model
            if not model_name in response:
                response[model_name] = {}
            response[model_name][name] = {
                'model_name': model_name,
                'model_id': model_id,
                'name': name,
                'field_description': field_description,
                'ttype': ttype,
                'relation': relation,
                'relation_field': relation_field,
                'readonly': readonly,
                'required': required,
                'relation_table': relation_table,
                'column1': column1,
                'column2': column2
            }

        return json.dumps(response)
