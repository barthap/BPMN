from collections import Counter
from typing import Dict, Set

from bpmn_network import BPMNNetwork


def from_simple_direct_succession(direct_succession: Dict[str, Set[str]]) -> BPMNNetwork:
    network = BPMNNetwork()

    for src, targets in direct_succession.items():
        network.add_node(src)
        for target in targets:
            network.add_node(target)
            network.add_edge(src, target)

    return network


def from_counter_direct_succession(direct_succession: Dict[str, Counter],
                                   event_counter: Dict[str, int] = None) -> BPMNNetwork:
    network = BPMNNetwork()
    if event_counter is None:
        event_counter = {}

    for src, targets in direct_succession.items():
        src_count = event_counter[src] if src in event_counter else 0
        network.add_node(src, src_count)
        for target in targets:
            target_count = event_counter[target] if target in event_counter else 0
            network.add_node(target, cnt=target_count)
            network.add_edge(src, target, cnt=targets[target])

    return network
