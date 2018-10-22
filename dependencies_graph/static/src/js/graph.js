odoo.define('dependencies_graph.graph', function (require) {
    "use strict";

    var session = require('web.session');

    var w = window['dependencies_graph'] = {};
    
    var selector = '#graph';
    var options = {
        configure: {
            enabled: true,
            filter: 'layout',
            showButton: true
        },
        physics: {
            enabled: true
        }
    };

    w.get_js_services = function () {
        var services = {};
        _.each(window.odoo.__DEBUG__.services, function (value, key) {
            if (typeof value === 'function') {
                services[key] = value;
            }
            if (typeof value === 'object') {
                _.each(value, function (v, k) {
                    if (typeof v === 'function') {
                        var name = key.concat('.', k);
                        services[name] = v;
                    }
                })
            }
        });
        return services;
    };

    w.set_js_services = function () {
        var services = w.get_js_services();
        var module = $('#js-module');

        _.each(services, function (value, key) {
            module
                .append($("<option></option>")
                    .attr("value", key)
                    .text(key));
        });
        module.chosen({search_contains: true});
    };

    w.set_odoo_modules = function () {
        var module = $('#odoo-module');
        return session.rpc('/dependencies_graph/modules').done(function (result) {
            var deps = JSON.parse(result);
            _.each(deps, function (value, key) {
                module
                    .append($("<option></option>")
                        .attr("value", key)
                        .text(key));
            });
            module.chosen({search_contains: true});
        });
    };

    w.set_models = function () {
        var module = $('#odoo-model,#odoo-model-ignore');
        session.rpc('/dependencies_graph/models').done(function (result) {
            w.models = JSON.parse(result);
            _.each(w.models, function (value, key) {
                module
                    .append($("<option></option>")
                        .attr("value", key)
                        .text(key));
            });
            module.chosen({search_contains: true});
        });
    };

    w.generate = function () {
        var type = $('#type').val();
        var odoo_module = $('#odoo-module').val();
        var js_services = $('#js-module').val();
        var odoo_model = $('#odoo-model').val();
        var acyclic_graph = $('#acyclic-graph:checked').length === 1;
        var module;

        if (_.contains(['module_parents', 'module_children'], type)) {
            module = odoo_module;
        }
        if (_.contains(['models_graph'], type)) {
            module = odoo_model;
        }
        if (_.contains(['js_parents', 'js_children'], type)) {
            module = js_services;
        }

        window.dependencies_graph[type](module, acyclic_graph).done(function () {
            console.log('generated', type, module);
        });
    };

    w.type_changed = function () {
        var type = $('#type').val();
        var odoo_module_options = $('#odoo-module-options');
        var js_service_options = $('#js-service-options');
        var odoo_model_options = $('#odoo-model-options');

        switch (type) {
            case 'module_parents':
            case 'module_children':
                odoo_module_options.show();
                js_service_options.hide();
                odoo_model_options.hide();
                w.set_odoo_modules();
                break;
            case 'models_graph':
                odoo_module_options.hide();
                js_service_options.hide();
                odoo_model_options.show();
                w.set_models();
                break;
            case 'js_parents':
            case 'js_children':
                odoo_module_options.hide();
                js_service_options.show();
                odoo_model_options.hide();
                w.set_js_services();
                break;
        }
    };

    $(w.type_changed);

    w.module_children = function (module, acyclic_graph) {
        var promise = $.Deferred();
        session.rpc('/dependencies_graph/modules').done(function (result) {
            var deps = JSON.parse(result);
            var nodes = new vis.DataSet([]);
            var edges = new vis.DataSet([]);

            var modules = [module];
            while (modules.length > 0) {
                var m = modules.shift();
                var children = _.filter(_.keys(deps), function (k) {
                    return _.contains(deps[k]['depends'], m);
                });
                modules = _.union(modules, children);

                nodes.update({
                    id: m,
                    label: m,
                    color: deps[m]['state'] === 'installed' ? '#97c2fc' : '#ff797f',
                    title: w.generate_module_tooltip(deps[m])
                });
                _.each(children, function (child) {
                    if (!(acyclic_graph && nodes.get(child))) {
                        nodes.update({
                            id: child,
                            label: child,
                            color: deps[child]['state'] === 'installed' ? '#97c2fc' : '#ff797f',
                            title: w.generate_module_tooltip(deps[child])
                        });
                        edges.update({from: m, to: child, arrows: 'to'})
                    }
                })
            }

            // create a network
            var container = $(selector)[0];
            var data = {
                nodes: nodes,
                edges: edges
            };
            $('#settings').empty();
            options['configure']['container'] = $('#settings')[0];
            var network = new vis.Network(container, data, options);

            promise.resolve(network);
        });
        return promise;
    };

    w.module_parents = function (module, acyclic_graph) {
        var promise = $.Deferred();
        session.rpc('/dependencies_graph/modules').done(function (result) {
            var deps = JSON.parse(result);
            var nodes = new vis.DataSet([]);
            var edges = new vis.DataSet([]);

            var modules = [module];
            while (modules.length > 0) {
                var m = modules.shift();
                var parents = deps[m]['depends'];
                modules = _.union(modules, parents);

                nodes.update({
                    id: m,
                    label: m,
                    color: deps[m]['state'] === 'installed' ? '#97c2fc' : '#ff797f',
                    title: w.generate_module_tooltip(deps[m])
                });
                _.each(parents, function (p) {
                    if (!(acyclic_graph && nodes.get(p))) {
                        nodes.update({
                            id: p,
                            label: p,
                            color: deps[p]['state'] === 'installed' ? '#97c2fc' : '#ff797f',
                            title: w.generate_module_tooltip(deps[p])
                        });
                        edges.update({from: p, to: m, arrows: 'to'})
                    }
                })
            }

            // create a network
            var container = $(selector)[0];
            var data = {
                nodes: nodes,
                edges: edges
            };
            $('#settings').empty();
            options['configure']['container'] = $('#settings')[0];
            var network = new vis.Network(container, data, options);

            promise.resolve(network);
        });
        return promise;
    };

    w.models_graph = function (models, acyclic_graph) {
        var nodes = new vis.DataSet([]);
        var edges = new vis.DataSet([]);
        var ignore = $('#odoo-model-ignore').val() || [];
        var processed = ignore.slice(); // copy
        var depth = parseInt($('#odoo-model-depth').val() || 1);

        var level = [models || []];
        for (var i = 0; i < depth; i++) {
            level.push([]);
            while (level[i].length > 0) {
                var model = level[i].shift();
                processed.push(model);
                var relations = _.filter(w.models[model], function (v, k) {
                    return _.contains(['one2many', 'many2one', 'many2many'], v['ttype'])
                        && !_.contains(ignore, v['relation']);
                });
                level[i + 1] = _.union(level[i + 1], _.difference(_.map(relations, r => r['relation']), processed));

                nodes.update({
                    id: model,
                    label: model,
                    title: w.generate_model_node_tooltip(w.models[model])
                });
                _.each(relations, function (rel) {
                    nodes.update({
                        id: rel['relation'],
                        label: rel['relation'],
                        title: w.generate_model_node_tooltip(w.models[rel['relation']])
                    });
                    edges.update({
                        from: model,
                        to: rel['relation'],
                        arrows: rel['ttype'] === 'many2one' ? 'to' :
                            (rel['ttype'] === 'one2many' ? 'from' : 'from,to'),
                        title: w.generate_model_edge_tooltip(rel)
                    })
                });
            }
        }

        // create a network
        var container = $(selector)[0];
        var data = {
            nodes: nodes,
            edges: edges
        };
        $('#settings').empty();
        options['configure']['container'] = $('#settings')[0];
        var network = new vis.Network(container, data, options);

        return $.Deferred().resolve(network);
    };

    w.js_graph = function (module, dependencies) {
        var promise = $.Deferred();
        var nodes = new vis.DataSet([]);
        var edges = new vis.DataSet([]);
        var services = w.get_js_services();

        var modules = _.pairs(_.pick(services, module));

        while (modules.length > 0) {
            var m = modules.pop()
            var x = m[0];
            var x_value = m[1];
            nodes.update({id: x, label: x, title: w.generate_js_tooltip(x_value)});
            _.each(services, function (y_value, y) {
                if (dependencies) { // parents
                    if (x_value.prototype && Object.getPrototypeOf(x_value.prototype).constructor === y_value) {
                        nodes.update({id: y, label: y, title: w.generate_js_tooltip(y_value)});
                        edges.add({from: y, to: x, arrows: 'to'});

                        modules.push([y, y_value]);
                    }
                } else {
                    if (y_value.prototype && Object.getPrototypeOf(y_value.prototype).constructor === x_value) {
                        nodes.update({id: y, label: y, title: w.generate_js_tooltip(y_value)});
                        edges.add({from: x, to: y, arrows: 'to'});

                        modules.push([y, y_value]);
                    }
                }
            });
        }

        // create a network
        var container = $(selector)[0];
        var data = {
            nodes: nodes,
            edges: edges
        };
        $('#settings').empty();
        options['configure']['container'] = $('#settings')[0];
        var network = new vis.Network(container, data, options);

        promise.resolve(network);
        return promise;
    };

    w.js_parents = function (module, acyclic_graph) {
        return w.js_graph(module, true);
    };

    w.js_children = function (module, acyclic_graph) {
        return w.js_graph(module, false);
    };

    w.generate_js_tooltip = function (f) {
        var e = $('<dl class="dl-horizontal"></dl>');
        _.each(f.prototype, function (value, key) {
            e.append($('<dt>' + key + ':</dt>'));

            if (_.isFunction(value)) {
                var str = value.toString();
                str = str.substr(0, str.indexOf(')') + 1);
                e.append($('<dd>' + str + '</dd>'))
            }
            else if (_.isObject(value)) {
                delete value['_super'];
                e.append($('<dd>' + JSON.stringify(value) + '</dd>'))
            } else {
                e.append($('<dd>' + value + '</dd>'))
            }
        });
        return e[0];
    };

    w.generate_module_tooltip = function (node) {
        var e = '<dl class="dl-horizontal">' +
            '<dt>name:</dt><dd>' + node['name'] + '</dd>' +
            '<dt>state:</dt><dd>' + node['state'] + '</dd>' +
            '</dl>';
        return e;
    };

    w.generate_model_edge_tooltip = function (rel) {
        var e = '<dl class="dl-horizontal">' +
            '<dt>model name (self):</dt><dd>' + rel['model_name'] + '</dd>' +
            '<dt>field name:</dt><dd>' + rel['name'] + '</dd>' +
            '<dt>field description:</dt><dd>' + rel['field_description'] + '</dd>' +
            '<dt>type:</dt><dd>' + rel['ttype'] + '</dd>' +
            '<dt>relation:</dt><dd>' + rel['relation'] + '</dd>' +
            '<dt>relation field:</dt><dd>' + rel['relation_field'] + '</dd>' +
            '<dt>relation table:</dt><dd>' + rel['relation_table'] + '</dd>' +
            '<dt>column 1:</dt><dd>' + rel['column1'] + '</dd>' +
            '<dt>column 2:</dt><dd>' + rel['column2'] + '</dd>' +
            '</dl>';
        return e;
    };

    w.generate_model_node_tooltip = function (model) {
        var fields = '';
        _.each(model, function (v, k) {
            fields += '<dt>' + k + ':</dt><dd>' +
                [v['ttype'],
                    v['required'] ? '[required]' : '',
                    v['readonly'] ? '[readonly]' : '',
                    v['field_description']].join(' ') +
                '</dd>'
        });

        var e = '<dl class="dl-horizontal">' +
            fields +
            '</dl>';
        return e;
    };
});
