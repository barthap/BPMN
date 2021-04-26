from collections import Counter
from typing import Dict, Set, List, Tuple

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

    evt_cntr = import_result.ev_counter if isinstance(import_result, CsvResult) else None
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


def from_filtered_import(import_res: Result, filtered_direct_succession: Dict[str, Dict[str, float]], filtered_out_two_loop: Dict[str, Dict[str, float]],
                         parallel_tuples: List[Tuple[str, str]], self_loop_events: List[str]):
    network = BPMNNetwork()

    for src, targets in filtered_direct_succession.items():

        def check_node_insert_parameters(src: str, filtered_direct_succession: Dict[str, Dict[str, float]], filtered_out_two_loop: Dict[str, Dict[str, float]],
                         parallel_tuples: List[Tuple[str, str]], self_loop_events: List[str]):
            self_looped = src in self_loop_events
            and_paralleled_with = set()
            for tup in parallel_tuples:
                if src in tup:
                    add_tab = []
                    for elem in tup:
                        if elem != src:
                            add_tab.append(elem)
                    and_paralleled_with.update(add_tab)

            is_in_two_loop_main = src in filtered_out_two_loop
            in_two_loop_feedback_with = set()
            for outside, out_dict in filtered_out_two_loop.items():
                if src in out_dict:
                    in_two_loop_feedback_with.update(outside)

            in_two_loop_feedback_with = in_two_loop_feedback_with if in_two_loop_feedback_with else None

            and_paralleled_with = None if (in_two_loop_feedback_with or is_in_two_loop_main) else and_paralleled_with

            is_end = src not in filtered_direct_succession
            is_start = bool(min([src not in successors for event, successors in filtered_direct_succession.items() if event != src]))

            return self_looped, and_paralleled_with, is_in_two_loop_main, in_two_loop_feedback_with, is_start, is_end


        node_insert_parameters = check_node_insert_parameters(src, filtered_direct_succession, filtered_out_two_loop, parallel_tuples, self_loop_events)

        network.add_node(src, cnt=import_res.ev_counter[src], self_looped=node_insert_parameters[0], and_paralleled_with=node_insert_parameters[1],
                         is_in_two_loop_main=node_insert_parameters[2], in_two_loop_feedback_with=node_insert_parameters[3], is_start=node_insert_parameters[4], is_end=node_insert_parameters[5])

        for target in targets:
            node_insert_parameters = check_node_insert_parameters(target, filtered_direct_succession, filtered_out_two_loop, parallel_tuples,
                                                                  self_loop_events)
            network.add_node(target, cnt=import_res.ev_counter[src], self_looped=node_insert_parameters[0],
                             and_paralleled_with=node_insert_parameters[1],
                             is_in_two_loop_main=node_insert_parameters[2],
                             in_two_loop_feedback_with=node_insert_parameters[3], is_start=node_insert_parameters[4],
                             is_end=node_insert_parameters[5])
            network.add_edge(src, target, cnt=import_res.direct_succession[src][target])

    return network