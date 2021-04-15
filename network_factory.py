from collections import Counter
from typing import Dict, Set

from bpmn_network import BPMNNetwork
from import_handler import Result, CsvResult


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


def from_importer(import_result: Result, import_start_end_events=False, autodetect_start_end_events=False) -> BPMNNetwork:
    assert not (import_start_end_events and autodetect_start_end_events), \
        "Choose either importing start/end events or autodetection. You cannot select both!"

    evt_cntr = import_result.event_counter if isinstance(import_result, CsvResult) else None
    network = from_counter_direct_succession(import_result.direct_succession, evt_cntr)

    if import_start_end_events:
        for e in import_result.start_events:
            network.nodes[e].is_start_node = True

        for e in import_result.end_events:
            network.nodes[e].is_end_node = True
    elif autodetect_start_end_events:
        network.autodetect_start_nodes()
        network.autodetect_end_nodes()

    return network
