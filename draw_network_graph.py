# -*- coding: utf-8 -*-
# Based on http://matthiaseisen.com/articles/graphviz/
# Origin - Natasha Samoilenko's Python for network engineers course 

import sys

try:
    import graphviz as gv
except ImportError:
    print("Module graphviz needs to be installed")
    print("pip install graphviz")
    sys.exit()

styles = {
    "graph": {
        "label": "Network Map",
        "fontsize": "16",
        "fontcolor": "white",
        "bgcolor": "#3F3F3F",
        "rankdir": "BT",
    },
    "nodes": {
        "fontname": "Helvetica",
        "shape": "box",
        "fontcolor": "white",
        "color": "#006699",
        "style": "rounded,filled",
        "fillcolor": "#006699",
        "margin": "0.4",
    },
    "edges": {
        "style": "dashed",
        "color": "green",
        "arrowhead": "open",
        "fontname": "Courier",
        "fontsize": "14",
        "fontcolor": "white",
    },
}


def apply_styles(graph, styles):
    graph.graph_attr.update(("graph" in styles and styles["graph"]) or {})
    graph.node_attr.update(("nodes" in styles and styles["nodes"]) or {})
    graph.edge_attr.update(("edges" in styles and styles["edges"]) or {})
    return graph


def draw_topology(topology_dict, out_filename="img/topology", style_dict=styles):
    """
    topology_dict - dictionary with topology

    Example of topology_dict:
        {('R4', 'Eth0/1'): ('R5', 'Eth0/1'),
         ('R4', 'Eth0/2'): ('R6', 'Eth0/0')}

    represents topology:
    [ R5 ]-Eth0/1 --- Eth0/1-[ R4 ]-Eth0/2---Eth0/0-[ R6 ]

    The function generates topology in svg format
    and stores to file 'topology.svg' in 'img' directory.
    """
    nodes = set(
        [item[0] for item in list(topology_dict.keys()) + list(topology_dict.values())]
    )

    graph = gv.Graph(format="svg")

    for node in nodes:
        graph.node(node)

    for key, value in topology_dict.items():
        head, t_label = key
        tail, h_label = value
        graph.edge(head, tail, headlabel=h_label, taillabel=t_label, label=" " * 12)

    graph = apply_styles(graph, style_dict)
    filename = graph.render(filename=out_filename)
    print("Topology saved in", filename)

