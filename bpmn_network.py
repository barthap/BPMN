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
    LOOP_GATE = 3


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
            if node.type == NodeType.EVENT:
                result[node] = self.causalities_for_node(node)
        return result

    def autodetect_start_nodes(self, update_nodes=True) -> Set[Node]:
        """
        @deprecated
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
        @deprecated
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

    def build_self_loop(self, node: Node):
        assert node.is_self_loop(), f'Node {node} is not self loop!'

        # remove self-succession
        node.remove_successor(node)

        succ1 = next(iter(node.successors))

        self_cnt = self.edges[node.name][node.name].cnt
        succ_cnt = self.edges[node.name][succ1.name].cnt

        gate = UtilityNode(self, name=f'self_loop_{node.name}')
        gate.successors = set(node.successors)
        gate.kind = NodeKind.XOR
        gate.successors.add(node)
        gate.predecessors = {node}
        self.nodes[gate.name] = gate

        self.edges[node.name] = {gate.name: Edge(self, node, gate, cnt=self_cnt+succ_cnt)}
        self.edges[gate.name] = {
            succ1.name: Edge(self, gate, succ1, cnt=succ_cnt),
            node.name: Edge(self, gate, node, cnt=self_cnt)
        }
        node.successors = {gate}

    def build_short_loop(self, node: Node):
        assert node.is_short_loop(), f'Node {node} is not short loop!'

        # remove self-succession and make life easier
        self_cnt = 0
        if node.is_self_loop():
            node.remove_successor(node)
            self_cnt = self.edges[node.name][node.name].cnt

        pred = node.prev()
        succ = node.next()

        #self.insert_dummy_before(pred, f'dummy_before_shortlooped_{node.name}')

        succ_cnt = self.edges[node.name][succ.name].cnt
        pred_cnt = self.edges[pred.name][node.name].cnt
        over_cnt = self.edges[pred.name][succ.name].cnt

        # Nodes
        pre_gate = UtilityNode(self, name=f'shortloop_pre_{node.name}')
        post_gate = UtilityNode(self, name=f'shortloop_post_{node.name}')
        pre_gate.kind = NodeKind.XOR
        pre_gate.function = NodeFunction.LOOP_GATE
        post_gate.kind = NodeKind.XOR
        self.nodes[pre_gate.name] = pre_gate
        self.nodes[post_gate.name] = post_gate

        pre_gate.successors = {post_gate}
        pre_gate.predecessors = {node, pred}
        post_gate.predecessors = {pre_gate}
        post_gate.successors = {succ, node}
        node.predecessors = {post_gate}
        node.successors = {pre_gate}
        pred.successors = {pre_gate}
        succ.predecessors = {post_gate}

        # Edges
        del self.edges[node.name]
        del self.edges[pred.name][node.name]
        del self.edges[pred.name][succ.name]

        self.edges[pred.name][pre_gate.name] = Edge(self, pred, pre_gate, pred_cnt+over_cnt)
        self.edges[node.name] = {pre_gate.name: Edge(self, node, pre_gate, succ_cnt)}
        self.edges[post_gate.name] = {succ.name: Edge(self, post_gate, succ, cnt=over_cnt+succ_cnt),
                                      node.name: Edge(self, post_gate, node, pred_cnt)
                                      }
        self.edges[pre_gate.name] = {
            post_gate.name: Edge(self, pre_gate, post_gate, over_cnt),
        }

        self._validate_structure()

    def build_two_loop(self, node: Node):
        assert node.is_two_loop(), f'Node {node} is not short loop!'

        # remove self-succession and make life easier
        if node.is_self_loop():
            node.remove_successor(node)


        two = node.next()  # or node.prev(), doesnt matter
        two.remove_predecessor(node)
        two.remove_successor(node)

        self.insert_dummy_before(two, f'dummy_before_looped_{two.name}')

        preds = set(two.predecessors)
        succs = set(two.successors)

        cnts = {
            'preds': { two: sum(map(lambda p: self.edges[p.name][two.name].cnt, preds))},
            two: {  node: self.edges[two.name][node.name].cnt,
                    'succs': sum(map(lambda s: self.edges[two.name][s.name].cnt, succs))},
            node: { two: self.edges[node.name][two.name].cnt}
        }

        for s in succs:
            cnts[two][s] = self.edges[two.name][s.name].cnt
        for p in preds:
            cnts[p] = {}
            cnts[p][two] = self.edges[p.name][two.name].cnt
            del self.edges[p.name][two.name]
        del self.edges[two.name]
        del self.edges[node.name]


        pre_gate = UtilityNode(self, name=f'twoloop_pre_{node.name}')
        post_gate = UtilityNode(self, name=f'twoloop_post_{node.name}')
        pre_gate.kind = NodeKind.XOR
        post_gate.kind = NodeKind.XOR
        self.nodes[pre_gate.name] = pre_gate
        self.nodes[post_gate.name] = post_gate

        for p in preds:
            p.successors = {pre_gate}

        pre_gate.predecessors = set(preds)
        pre_gate.predecessors.add(node)
        pre_gate.successors = {two}
        two.predecessors = {pre_gate}
        two.successors = {post_gate}
        post_gate.predecessors = {two}
        post_gate.successors = set(succs)
        post_gate.successors.add(node)

        for s in succs:
            s.predecessors = {post_gate}
        node.predecessors = {post_gate}
        node.successors={pre_gate}

        for p in preds:
            self.edges[p.name][pre_gate.name] = Edge(self, p, pre_gate, cnt=cnts[p][two])
        self.edges[pre_gate.name] = {two.name: Edge(self, pre_gate, two, cnt=cnts['preds'][two] + cnts[node][two])}
        self.edges[two.name] = {post_gate.name: Edge(self, two, post_gate, cnt=cnts[two]['succs'] + cnts[two][node])}
        self.edges[node.name] = {pre_gate.name: Edge(self, node, pre_gate, cnt=cnts[node][two])}
        self.edges[post_gate.name] = {}
        self.edges[post_gate.name][node.name] = Edge(self, post_gate, node, cnt=cnts[two][node])
        for s in succs:
            self.edges[post_gate.name][s.name] = Edge(self, post_gate, s, cnt=cnts[two][s])

        self._validate_structure()

    def process_short_loops(self):
        nodes = set(self.nodes.values())    # copy to avoid weird errors
        for node in nodes:
            if node.is_two_loop():
                self.build_two_loop(node)
            elif node.is_short_loop():
                self.build_short_loop(node)
            elif node.is_self_loop():
                self.build_self_loop(node)
