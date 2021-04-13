from copy import deepcopy

from bpmn_network import BPMNNetwork


def filter_edges(network: BPMNNetwork, threshold: int) -> BPMNNetwork:
    """
    Sets is_filtered_out=True for edges with cnt < threshold
    """
    new_network = deepcopy(network)

    for edge in new_network.get_edge_list():
        if edge.cnt < threshold:
            edge.is_filtered_out = True

    return new_network


def filter_events(network: BPMNNetwork, threshold: int) -> BPMNNetwork:
    """
    Sets is_filtered_out=True for events (nodes) with cnt < threshold
    """
    new_network = deepcopy(network)

    for event in new_network.nodes.values():
        if event.cnt < threshold:
            event.is_filtered_out = True

    return new_network


def find_broken_nodes(network: BPMNNetwork):
    """
    Można użyć BFS / DFS do szukania urwanych ścieżek
    czyli jak jakiś event został samotny bez krawędzi po filtracji
    :param network:
    :return:
    """
    pass
