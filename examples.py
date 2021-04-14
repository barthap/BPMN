from pprint import pprint

from more_itertools import pairwise

import network_factory
from bpmn_network import alpha_miner
from import_handler import import_handler
from drawing import draw_simple_network
from filters import filter_edges, filter_events


def lab1_repair_example():
    """
    Przyklad z pierwszych labow z repairem
    Bez bram, tylko filtry
    """
    repair_example = import_handler('data/repairExample.csv')

    network = network_factory.from_counter_direct_succession(repair_example.direct_succession,
                                                             repair_example.event_counter)

    # example on how to manually set start/end events
    for e in repair_example.start_events:
        network.nodes[e].is_start_node = True

    for e in repair_example.end_events:
        network.nodes[e].is_end_node = True

    filtered_network = filter_edges(network, threshold=400)
    filtered_network = filter_events(filtered_network, threshold=700)
    filtered_network.delete_filtered_out_items()

    # filtered_network.autodetect_start_nodes()
    # filtered_network.autodetect_end_nodes()

    draw_simple_network(filtered_network, ortho=False, with_numbers=True, auto_show=True,
                        name='repair_simple', title='Lab 1 Repair Example')


def lab2_example():
    """
    Przyklad zrobiony przez niego z lab 2
    """
    direct_succession = {
        'a': {'b', 'c'},
        'b': {'c', 'd'},
        'c': {'b', 'd'},
        'd': {'e', 'f'},
        'e': {'g'},
        'f': {'g'},
        'g': {}
    }
    network = network_factory.from_simple_direct_succession(direct_succession)
    network.autodetect_start_nodes()
    network.autodetect_end_nodes()

    processed_network = alpha_miner(network)

    draw_simple_network(processed_network, name='lab2_example', title='Lab 2 przyklad')


def lab2_ex1():
    """
    Cwiczenie 1 z lab 2
    Kilka logow i ma utworzyc siec i bramy
    """
    test_example = ['a b c d e h i k', 'a b d c e h j k', 'a f g h i k']

    def my_direct_succession(logtable):
        dictionary = dict()
        for entry in logtable:
            for previous, event in pairwise(entry.split(' ')):
                if previous not in dictionary:
                    dictionary[previous] = set()
                dictionary[previous].add(event)
            if entry.split(' ')[-1] not in dictionary:
                dictionary[entry.split(' ')[-1]] = set()

        return dictionary

    direct_succession = my_direct_succession(test_example)

    network = network_factory.from_simple_direct_succession(direct_succession)
    network.autodetect_start_nodes()
    network.autodetect_end_nodes()

    processed_network = alpha_miner(network)

    draw_simple_network(processed_network, name='lab2_ex1', title='Lab 2 cwiczenie 1')


def lab2_ex2():
    repair_example = import_handler('data/repairExample.csv')

    network = network_factory.from_counter_direct_succession(repair_example.direct_succession,
                                                             repair_example.event_counter)

    # Filtruje najpierw a dopiero potem robie mining, tak latwiej
    # On mówił o innym podejściu ale nie pamiętam
    filtered_network = filter_edges(network, threshold=400)
    filtered_network = filter_events(filtered_network, threshold=700)
    filtered_network.delete_filtered_out_items()

    print(filtered_network.are_nodes_parallel('Inform User', 'Test Repair'))
    bpmn_network = alpha_miner(filtered_network)
    bpmn_network.autodetect_start_nodes()
    bpmn_network.autodetect_end_nodes()

    draw_simple_network(bpmn_network, with_numbers=True, auto_show=True,
                        name='repair_lab2', title='Lab 2 Repair BPMN')


def lab2_setA(case: int):
    a1_example = import_handler('data/A'+str(case)+'.csv', sep=";")

    network = network_factory.from_counter_direct_succession(a1_example.direct_succession,
                                                             a1_example.event_counter)

    filtered_network = filter_edges(network, threshold=0)
    filtered_network = filter_events(filtered_network, threshold=0)
    filtered_network.delete_filtered_out_items()

    bpmn_network = alpha_miner(filtered_network)

    bpmn_network.autodetect_start_nodes()
    bpmn_network.autodetect_end_nodes()

    draw_simple_network(bpmn_network, with_numbers=True, auto_show=True,
                        name='A'+str(case), title='A'+str(case))