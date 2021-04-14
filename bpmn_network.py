from copy import deepcopy
from enum import Enum
from math import inf
from pprint import pprint
from typing import Set, Dict, Union

from more_itertools import pairwise

from network import Network, Node, NodeType, Edge


class NodeKind(Enum):
    UNKNOWN = 0
    AND = 1  # to jest chyba plus
    XOR = 2  # to jest chyba krzyzyk


class NodeFunction(Enum):
    ANY = 0
    SPLIT = 1
    MERGE = 2


class UtilityNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cnt = inf  # do not filter out these nodes
        self.type = NodeType.UTILITY
        self.kind = NodeKind.UNKNOWN
        self.function = NodeFunction.ANY

    def _validate_function(self):
        if self.function == NodeFunction.SPLIT:
            assert self.is_split() and not self.is_merge(), \
                f"Node {self} has function SPLIT but does not satisfy connection constraints"
        elif self.function == NodeFunction.MERGE:
            assert self.is_merge() and not self.is_split(), \
                f"Node {self} has function MERGE but does not satisfy connection constraints"

    def __repr__(self):
        return f'[{self.kind} ({self.function})]'


def _get_split_gate_name(source: Node, targets: Set[Node], kind: NodeKind):
    return f'{kind}_s_{source.name}->[{",".join(map(lambda t: t.name, targets))}]'


def _get_merge_gate_name(sources: Set[Node], target: Node, kind: NodeKind):
    return f'{kind}_m_[{",".join(map(lambda s: s.name, sources))}]->{target.name}'


class BPMNNetwork(Network):
    def __init__(self):
        super().__init__()

    def insert_split_node_between(self, source: Node, targets: Set[Node], kind: NodeKind):
        # TODO: add assertions
        name = _get_split_gate_name(source, targets, kind)
        new_node = UtilityNode(network=self, name=name)
        new_node.function = NodeFunction.SPLIT
        new_node.kind = kind
        new_node.predecessors.add(source)
        new_node.successors.update(targets)
        self.nodes[name] = new_node
        self.edges[name] = {}

        aggregated_cnt = 0
        for target in targets:
            if target not in source.successors:
                print(f"WARN: {target.name} not in {source.name} successors\n\twhen creating {name}, skipping...")
                continue

            cnt = self.edges[source.name][target.name].cnt
            aggregated_cnt += cnt

            # remove old edge
            source.remove_successor(target)
            del self.edges[source.name][target.name]

            # add new edge
            target.predecessors.add(new_node)
            self.edges[new_node.name][target.name] = Edge(self, new_node, target, cnt=cnt)

        # create new connection source->gate
        source.successors.add(new_node)
        self.edges[source.name][new_node.name] = Edge(self, source, new_node, cnt=aggregated_cnt)

        self._validate_structure()

    def insert_merge_node_between(self, sources: Set[Node], target: Node, kind: NodeKind):
        # TODO: add assertions
        name = _get_merge_gate_name(sources, target, kind)
        new_node = UtilityNode(network=self, name=name)
        new_node.function = NodeFunction.MERGE
        new_node.kind = kind
        new_node.predecessors.update(sources)
        new_node.successors.add(target)
        self.nodes[name] = new_node

        aggregated_cnt = 0
        for source in sources:
            if source not in target.predecessors:
                print(f"WARN: {source.name} not in {target.name} predecessors\n\twhen creating {name}, skipping...")
                continue

            cnt = self.edges[source.name][target.name].cnt
            aggregated_cnt += cnt

            target.remove_predecessor(source)
            del self.edges[source.name][target.name]

            source.successors.add(new_node)
            self.edges[source.name][new_node.name] = Edge(self, source, new_node, cnt=cnt)

        # create new connection gate -> target
        target.predecessors.add(new_node)
        self.edges[new_node.name] = {}
        self.edges[new_node.name][target.name] = Edge(self, new_node, target, cnt=aggregated_cnt)

        self._validate_structure()

    def delete_parallelism(self, node1: Union[Node, str], node2: Union[Node, str]):
        if isinstance(node1, str):
            node1 = self.nodes[node1]
        if isinstance(node2, str):
            node2 = self.nodes[node2]

        if not self.are_nodes_parallel(node1, node2):
            print(f"WARN: {node1} and {node2} are not parallel, nothing to do")
            return

        node1.remove_successor(node2)
        node2.remove_successor(node1)
        del self.edges[node1.name][node2.name]
        del self.edges[node2.name][node1.name]

    def delete_parallelism_from_all(self, nodes: Set[Node]):
        pairs = pairwise(nodes)
        for node1, node2 in pairs:
            self.delete_parallelism(node1, node2)

    def is_causality(self, src: Union[Node, str], target: Union[Node, str]):
        if isinstance(src, str):
            src = self.nodes[src]
        if isinstance(target, str):
            target = self.nodes[target]

        return target in src.successors and src not in target.successors

    def are_nodes_parallel(self, node1: Union[Node, str], node2: Union[Node, str]):
        if isinstance(node1, str):
            node1 = self.nodes[node1]
        if isinstance(node2, str):
            node2 = self.nodes[node2]

        return node1 in node2.successors and node2 in node1.successors

    def are_all_nodes_parallel(self, nodes: Set[Node]):
        pairs = pairwise(nodes)
        results = list(map(lambda pair: self.are_nodes_parallel(pair[0], pair[1]), pairs))
        return all(results)

    def causalities_for_node(self, node: Union[Node, str]) -> Set[Node]:
        if isinstance(node, str):
            node = self.nodes[node]

        causalities = set(n for n in node.successors if n not in node.predecessors)

        return causalities

    def parallel_events_for_node(self, node: Union[Node, str]) -> Set[Node]:
        """
        Finds nodes parallel to provided node

        :param node: a `Node` or node name
        :return: a set of parallel nodes
        """
        if isinstance(node, str):
            node = self.nodes[node]

        return set(n for n in node.successors if n in node.predecessors)

    def get_causality(self) -> Dict[Node, Set[Node]]:
        """
        Returns causality almost the same way as during lab
        Each dict key is a node, and elements are set of directly succeeding nodes

        :return: dict Node -> set of succeeding nodes
        """
        result = {}
        for node in self.nodes.values():
            result[node] = self.causalities_for_node(node)
        return result

    def autodetect_start_nodes(self, update_nodes=True) -> Set[Node]:
        """
        Detects starting events based on connections
        (finds events with no predecessors)

        :param update_nodes: if True, nodes have automatically set `is_start_node = True`
        :return: found starting nodes
        """
        detected = set()
        for node in self.nodes.values():
            if len(node.predecessors) == 0:
                detected.add(node)
                if update_nodes:
                    node.is_start_node = True

        return detected

    def autodetect_end_nodes(self, update_nodes=True) -> Set[Node]:
        """
        Detects finishing events based on connections
        (finds events with no successors)

        :param update_nodes: if True, nodes have automatically set `is_end_node = True`
        :return: found ending nodes
        """
        detected = set()
        for node in self.nodes.values():
            if len(node.successors) == 0:
                detected.add(node)
                if update_nodes:
                    node.is_end_node = True

        return detected


def alpha_miner(network: BPMNNetwork) -> BPMNNetwork:
    """
    Alpha miner taki sam jak u nas w Lab 2
    Ale to jest jego wersja, tzn nie ma JESZCZE obsługi 2 bram bezpośrednio po sobie

    :return: Zwraca nowa siec z bramami
    """
    net = deepcopy(network)
    causality = net.get_causality()

    # jako że z sieci usuwam dodane parallel events na bieżąco
    # to przechowuje je tutaj, żeby mieć z czego zrobić merge
    parallelisms = list()

    # #Wychwytywanie połączeń brama-brama:
    # for event, successions in causality.items():
    #     prevs_tables = []
    #     for successor in successions:
    #         prevs_tables.append(successor.predecessors)
    #     unique_prevs_table = []
    #     for element in prevs_tables:
    #         temp_element = {entry for entry in element if entry not in successions}
    #         if temp_element not in unique_prevs_table:
    #             unique_prevs_table.append(temp_element)
    #     if len(unique_prevs_table) == 1:
    #         net.add_node('temp')
    #         if net.are_all_nodes_parallel(successions):
    #             parallelisms += [successions]
    #             net.delete_parallelism_from_all(successions)
    #             for successor in successions:
    #                 net.add_edge(net.nodes['temp'].name,successor.name)
    #             net.insert_split_node_between(net.nodes['temp'], successions, kind=NodeKind.AND)
    #         else:
    #             for successor in successions:
    #                 net.add_edge(net.nodes['temp'].name,successor.name)
    #             net.insert_split_node_between(net.nodes['temp'], successions, kind=NodeKind.XOR)
    #         if unique_prevs_table[0] in parallelisms:
    #             for prev in unique_prevs_table[0]:
    #                 net.add_edge(prev.name, net.nodes['temp'].name)
    #             net.insert_merge_node_between(unique_prevs_table[0], net.nodes['temp'], kind=NodeKind.AND)
    #         else:
    #             for prev in unique_prevs_table[0]:
    #                 net.add_edge(prev.name, net.nodes['temp'].name)
    #             net.insert_merge_node_between(unique_prevs_table[0], net.nodes['temp'], kind=NodeKind.XOR)
    #         net.delete_node_merge_edges(net.nodes['temp'])
    #     else:
    #         pass


    # Pierwszy for od niego
    for event, successions in causality.items():
        if len(successions) > 1:
            if net.are_all_nodes_parallel(successions):
                parallelisms += [successions]
                net.delete_parallelism_from_all(successions)
                net.insert_split_node_between(event, successions, kind=NodeKind.AND)
            else:
                net.insert_split_node_between(event, successions, kind=NodeKind.XOR)

    # Drugi for do niego
    # nie uzywam inv_causality bo mam swoje narzedzia od tego
    for node in set(net.nodes.values()):
        if not node.is_merge(): # to załatwia inv causality
            continue

        prevs = set(node.predecessors) # we need to copy
        if prevs in parallelisms:
            net.insert_merge_node_between(prevs, node, kind=NodeKind.AND)
        else:
            net.insert_merge_node_between(prevs, node, kind=NodeKind.XOR)

    return net
