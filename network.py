from __future__ import annotations

from enum import Enum
from typing import List, Dict, Set, Union


class NodeType(Enum):
    EVENT = 0
    UTILITY = 1
    DUMMY = 2  # dummy node, not drawable


class Node:
    def __init__(self, network: Network, name: str, cnt: int = 0, is_start=False, is_end=False):
        self.network = network
        self.name = name
        self.cnt = cnt
        self.predecessors: Set[Node] = set()
        self.successors: Set[Node] = set()
        self.is_filtered_out = False
        self.is_start_node = is_start
        self.is_end_node = is_end
        self.type = NodeType.EVENT

    def is_event(self):
        return self.type == NodeType.EVENT

    def is_dummy(self):
        return self.type == NodeType.DUMMY

    def is_split(self) -> bool:
        """
        :return: True if node has more than one successor
        """
        filtered = list(filter(lambda p: p.type == NodeType.EVENT, self.successors))
        return len(filtered) > 1

    def is_merge(self) -> bool:
        """
        :return: True if node has more than one predecessor
        """
        filtered = list(filter(lambda p: p.type == NodeType.EVENT, self.predecessors))
        return len(filtered) > 1

    def is_self_loop(self) -> bool:
        """
        Picture 1 - Self is connected to self
        """
        return self in self.successors  # and len(self.successors.intersection(self.predecessors)) == 0

    def is_short_loop(self) -> bool:
        """
        Checks if this node should be short-looped.
        Given self node as A, detects it its such situation
        X -> Y
        X -> A -> Y
        X -> A -> A -> Y
        """
        filter_out_self = lambda x: set(t for t in x if t is not self)
        succ = filter_out_self(self.successors)
        pred = filter_out_self(self.predecessors)
        if len(succ) != 1 or len(pred) != 1:
            return False

        x = next(iter(pred))
        y = next(iter(succ))
        return y in x.successors

    def is_two_loop(self) -> bool:
        """
        Checks if event is like B event in situation on pic 3
        :return:
        """
        filter_out_self = lambda x: set(t for t in x if t is not self)
        succ = filter_out_self(self.successors)
        pred = filter_out_self(self.predecessors)
        if len(succ) != 1 or len(pred) != 1:
            return False

        return pred == succ

    def next(self) -> Node:
        """
        If node has only one successor, it accesses it
        """
        assert not self.is_split(), f"Node {self} must have only one successor in order to use next()"
        return next(iter(self.successors))

    def prev(self) -> Node:
        """
        If node has only one predecessor, it accesses it
        """
        assert not self.is_merge(), f"Node {self} must have only one predecessor in order to use prev()"
        return next(iter(self.predecessors))

    def remove_successor(self, successor_to_remove: Node):
        if successor_to_remove not in self.successors:
            raise Exception(f'{successor_to_remove} is not a successor of {self}, cannot remove!')

        successor_to_remove.predecessors.remove(self)
        self.successors.remove(successor_to_remove)

    def remove_predecessor(self, predecessor_to_remove: Node):
        if predecessor_to_remove not in self.predecessors:
            raise Exception(f'{predecessor_to_remove} is not a precedessor of {self}, cannot remove!')

        predecessor_to_remove.successors.remove(self)
        self.predecessors.remove(predecessor_to_remove)

    def remove_all_successors(self):
        for successor in set(self.successors):
            self.remove_successor(successor)

    def remove_all_predecessors(self):
        for predecessor in set(self.predecessors):
            self.remove_predecessor(predecessor)

    def __repr__(self):
        return f'[Node: {self.name}]'

    def __str__(self):
        return f'{self.name} ({self.cnt})'


class Edge:
    def __init__(self, network: Network, src: Node, target: Node, cnt: int = 0):
        self.network = network
        self.src = src
        self.target = target
        self.cnt = cnt
        self.is_filtered_out = False

    def __repr__(self):
        return f'[{self.src.name}->{self.target.name} ({self.cnt})]'

    def __str__(self):
        return f'{self.cnt}'


class Network:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Dict[str, Edge]] = {}

    def add_node(self, name: str, cnt=0, overwrite=False, is_start=False, is_end=False):
        if overwrite or name not in self.nodes:
            self.nodes[name] = Node(self, name, cnt, is_start, is_end)

    def add_edge(self, src: str, target: str, cnt=0):
        if not (src in self.nodes and target in self.nodes):
            raise Exception(f"Cannot add edge {src}->{target}, source and target both have to exist")

        src_node = self.nodes[src]
        target_node = self.nodes[target]

        src_node.successors.add(target_node)
        target_node.predecessors.add(src_node)
        if src not in self.edges:
            self.edges[src] = {}
        self.edges[src][target] = Edge(self, src_node, target_node, cnt)

    def get_edge_list(self) -> List[Edge]:
        return [edge for edge_src in self.edges for edge in self.edges[edge_src].values()]

    def get_start_events(self) -> Set[Node]:
        """
        Gets nodes with `is_start_node = True`
        """
        return set(x for x in self.nodes.values() if x.is_start_node)

    def get_end_events(self) -> Set[Node]:
        """
        Gets nodes with `is_end_node = True`
        """
        return set(x for x in self.nodes.values() if x.is_end_node)

    def delete_node(self, node: Node):
        node.remove_all_successors()
        node.remove_all_predecessors()

        del self.edges[node.name]
        for edge_list in self.edges.values():
            if node.name in edge_list:
                del edge_list[node.name]

        del self.nodes[node.name]

    def delete_edge(self, edge: Edge):
        edge.src.remove_successor(edge.target)
        del self.edges[edge.src.name][edge.target.name]

    def delete_filtered_out_items(self):
        """
        Deletes all nodes and edges marked as `filtered_out`
        """

        # delete nodes
        nodes_to_purge = set()
        for node in self.nodes.values():
            if node.is_filtered_out:
                nodes_to_purge.add(node)

        for node in nodes_to_purge:
            self.delete_node(node)

        # delete edges
        for edge in self.get_edge_list():
            if edge.is_filtered_out:
                self.delete_edge(edge)

        self._validate_structure()  # to be sure if its alright

    def delete_node_merge_edges(self, node: Node):
        """
        Given nodes: A->B->C
        Deletes node B and merges into A->C
        Deleted node can only have single predecessor and successor

        :param node: Node to delete
        """
        edge_cnt = self.edges[node.prev().name][node.name].cnt
        self.edges[node.prev().name][node.next().name] = Edge(self, node.prev(), node.next(), edge_cnt)

        node.prev().successors.add(node.next())
        node.next().predecessors.add(node.prev())
        self.delete_node(node)

    def insert_dummy_before(self, node: Node, dummy_name: str) -> Node:
        """
        Inserts dummy before provided node, updates connections.
        """
        dummy = Node(self, name=dummy_name, cnt=0)
        dummy.type = NodeType.DUMMY
        dummy.predecessors = set(node.predecessors)
        dummy.successors = {node}
        node.predecessors = {dummy}
        self.nodes[dummy_name] = dummy

        self.edges[dummy_name] = {node.name: Edge(self, dummy, node, 0)}
        for d in dummy.predecessors:
            d.successors.remove(node)
            d.successors.add(dummy)
            original_cnt = self.edges[d.name][node.name].cnt
            self.edges[d.name][dummy_name] = Edge(self, d, dummy, original_cnt)
            del self.edges[d.name][node.name]

        return dummy

    def insert_dummy_after(self, node: Node, dummy_name: str) -> Node:
        dummy = Node(self, name=dummy_name, cnt=0)
        dummy.type = NodeType.DUMMY
        dummy.successors = set(node.successors)
        dummy.predecessors = {node}
        node.successors = {dummy}
        self.nodes[dummy_name] = dummy

        self.edges[node.name][dummy_name] = Edge(self, node, dummy, 0)
        self.edges[dummy_name] = {}
        for s in dummy.successors:
            s.predecessors.remove(node)
            s.predecessors.add(dummy)
            original_cnt = self.edges[node.name][s.name].cnt
            self.edges[dummy_name][s.name] = Edge(self, dummy, s, original_cnt)
            del self.edges[node.name][s.name]

        return dummy

    def _validate_structure(self):
        """
        Validates if pretty complicated and fragile network schema is not corrupt
        """
        for node in self.nodes.values():
            for successor in node.successors:
                assert node in successor.predecessors, \
                    f'Net invalid! {successor} not in {node} predecessors, but vice versa!'
                edge = self.edges[node.name][successor.name]
                assert edge.src == node and edge.target == successor, f'Edge {edge} doesnt match real network state!'

            for predecessor in node.predecessors:
                assert node in predecessor.successors, \
                    f'Net invalid! {predecessor} not in {node} successors, but vice versa!'
                edge = self.edges[predecessor.name][node.name]
                assert edge.src == predecessor and edge.target == node, f'Edge {edge} doesnt match real network state!'

            # ## IF START/END EVENTS ARE PARALLEL, THEN THESE ASSERTIONS ARE NOT VALID
            # if node.is_start_node:
            #     assert len(node.predecessors) == 0,\
            #         f'Node {node} is marked as starting, but has precedessors: {node.predecessors}'
            #
            # if node.is_end_node:
            #     assert len(node.successors) == 0,\
            #         f'Node {node} is marked as ending, but has successors: {node.successors}'
