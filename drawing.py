from bpmn_network import UtilityNode, NodeKind
from network import Network, NodeType
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import pygraphviz as pgv

AND_LABEL = '+'
XOR_LABEL = 'x'


def _draw_utility_node(G: pgv.AGraph, name, label='?'):
    G.add_node(name, shape="diamond",
               width=".7", height=".7",
               fixedsize="true",
               fontsize="40", label=label)


def draw_simple_network(network: Network,
                        name='graph',
                        title='Process Diagram',
                        auto_show=False,
                        with_numbers=False,
                        ortho=True,
                        draw_filtered_out=False,
                        draw_start_end_circles=True):
    """
    Draws a BPMN process diagram using PyGraphViz

    :param network: a Network to render
    :param name: unique name if multiple renders at time - it is saved to {name}.png
    :param title: Title to display
    :param auto_show: If true, it calls `plt.show()`
    :param numbers: Show event and edge count on labels
    :param ortho: Draw edges only orthogonal
    :param draw_filtered_out: Draw filtered-out edges
    :param draw_start_end_circles: Draw start and end event circle
    """
    G = pgv.AGraph(strict=False, directed=True)
    G.graph_attr['rankdir'] = 'LR'
    G.node_attr['shape'] = 'Mrecord'
    if ortho:
        G.graph_attr['splines'] = 'ortho'
    G.graph_attr['nodesep'] = '0.8'
    G.edge_attr.update(penwidth='2')

    for node in network.nodes.values():
        if not draw_filtered_out and node.is_filtered_out:
            continue

        if node.type == NodeType.UTILITY:
            if not isinstance(node, UtilityNode):
                print(f'WARN: Node {node.name} is marked as utility but its not an UtilityNode instance!')
                _draw_utility_node(G, node.name)
                continue

            label = '?'
            if node.kind == NodeKind.AND:
                label = AND_LABEL
            elif node.kind == NodeKind.XOR:
                label = XOR_LABEL

            _draw_utility_node(G, node.name, label)
        else:
            label = node.__str__() if with_numbers else node.name
            G.add_node(node.name, label=label)

    for edge in network.get_edge_list():
        if not draw_filtered_out and edge.is_filtered_out:
            continue
        label = edge.__str__() if with_numbers else ''
        G.add_edge(edge.src.name, edge.target.name, label=label)

    if draw_start_end_circles:
        for i, start_evt in enumerate(network.get_start_events()):
            G.add_node(f'_start_{i}', shape="circle", label="")
            G.add_edge(f'_start_{i}', start_evt.name)

        for i, end_evt in enumerate(network.get_end_events()):
            G.add_node(f'_end_{i}', shape="circle", label="", penwidth='3')
            G.add_edge(end_evt.name, f'_end_{i}')

    G.layout()
    G.draw(f'results/{name}.png', prog='dot')
    img = mpimg.imread(f'results/{name}.png')
    plt.figure()
    plt.axis('off')
    plt.imshow(img)
    plt.title(title)
    if auto_show:
        plt.show()
