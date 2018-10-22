# Odoo Dependencies Graph

This tool is aimed to help software developers to get a better understanding of the dependencies among the modules 
and the models relationship in an Odoo application. It also shows the inheritance graph of JavaScript objects defined 
in Odoo.

The library [vis.js](http://visjs.org/) is used to render the graph.

## Types of graph

### Modules graph

1. Odoo Module Parents

    Given an Odoo module it shows every module in which the module depends on. These are the modules that need to be 
    installed before it.
    
2. Odoo Module Children

    Given an Odoo module it shows every module that depends of it directly or indirectly.
    
A module can have redundant dependencies. The option `Acyclic graph` shows or hides these redundant dependencies. 
    
### Models graph

Given some models it shows the relationship graph with other models.

Some models, for example `res.users`, have relations with all models. The option `Ignore` exclude some models
from the graph.

The option `Depth` specifies how deep the graph is going to be. A lower value is recommended.

### JS objects graph

1. JavaScript Parents

    Given some JavaScript constructor functions, the graph shows the functions (parents) which the given functions extend.
    
2. JavaScript Children

    Given some JavaScript constructor functions, the graph shows the functions (children) that extend the given functions.
    
# Autor web: 

https://github.com/adrian-chang-alcover/dependencies_graph
