from pprint import pprint

from more_itertools import pairwise

import filtering
import network_factory
from miner import alpha_miner
from import_handler import import_handler
from drawing import draw_simple_network
from filters import filter_edges, filter_events


def lab1_repair_example():
    """
    Przyklad z pierwszych labow z repairem
    Bez bram, tylko filtry
    """
    repair_example = import_handler('data/repairExample.csv')

    network = network_factory.from_importer(repair_example, import_start_end_events=True)

    filtered_network = filter_edges(network, threshold=400)
    filtered_network = filter_events(filtered_network, threshold=700)
    filtered_network.delete_filtered_out_items()

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

    network = network_factory.from_importer(repair_example)

    # Filtruje najpierw a dopiero potem robie mining, tak latwiej
    # On mówił o innym podejściu ale nie pamiętam
    filtered_network = filter_edges(network, threshold=400)
    filtered_network = filter_events(filtered_network, threshold=700)
    filtered_network.delete_filtered_out_items()

    filtered_network.autodetect_end_nodes()
    filtered_network.autodetect_start_nodes()

    print(filtered_network.are_nodes_parallel('Inform User', 'Test Repair'))
    bpmn_network = alpha_miner(filtered_network)

    draw_simple_network(bpmn_network, with_numbers=True, auto_show=True,
                        name='repair_lab2', title='Lab 2 Repair BPMN')


def lab2_setA(case: int):
    a1_example = import_handler('data/A'+str(case)+'.csv', sep=";")

    network = network_factory.from_importer(a1_example, import_start_end_events=True)

    filtered_network = filter_edges(network, threshold=0)
    filtered_network = filter_events(filtered_network, threshold=0)
    filtered_network.delete_filtered_out_items()

    bpmn_network = alpha_miner(filtered_network)

    #bpmn_network.autodetect_start_nodes()
    #bpmn_network.autodetect_end_nodes()

    draw_simple_network(bpmn_network, with_numbers=True, auto_show=True,
                        name='A'+str(case), title='A'+str(case))


def loop1():
    test_net_loop1 = {
        'X': {'A'},
        'A': {'A', 'Y'}
    }
    net = network_factory.from_simple_direct_succession(test_net_loop1)
    net.autodetect_start_nodes()
    net.autodetect_end_nodes()

    net = alpha_miner(net)

    draw_simple_network(net, name='self_loop1', title='Self loop')


def loop2():
    test_net_loop2 = {
        'X': {'A', 'Y'},
        'A': {'A', 'Y'}
    }
    net = network_factory.from_simple_direct_succession(test_net_loop2)
    net.autodetect_start_nodes()
    net.autodetect_end_nodes()

    net = alpha_miner(net)

    draw_simple_network(net, name='short_loop2', title='Short loop (pic 2)')


def loop3():
    test_net_loop3 = {
        'X': {'A'},
        'A': {'B', 'Y'},
        'B': {'A'},
    }
    net = network_factory.from_simple_direct_succession(test_net_loop3)
    net.autodetect_start_nodes()
    net.autodetect_end_nodes()

    net = alpha_miner(net)

    draw_simple_network(net, name='loop3', title='Loop (pic 3)')


def lab3_setB(case: int):
    example = import_handler('data/B'+str(case)+'.csv')
    SD_mat = filtering.calculate_significance_dependency_matrix(example)
    two_loop_mat = filtering.calculate_2loop_matrix(example)
    filter_thres = 0.9 if case in [4,5,6,8,9] else 0
    filtered_direct_succession, filtered_out_two_loop, parallel_tuples, self_loop_events = filtering.filter_network_by_matrices(SD_mat, two_loop_mat, filter_thres)

    filtered_network = network_factory.from_filtered_import(example, filtered_direct_succession, filtered_out_two_loop, parallel_tuples, self_loop_events)

    bpmn_network = alpha_miner(filtered_network)

    draw_simple_network(bpmn_network, with_numbers=True, auto_show=True,
                        name='B'+str(case), title='B'+str(case))


def lab3_setB_nofilter(case: int):
    a1_example = import_handler('data/B'+str(case)+'.csv', sep=",")

    network = network_factory.from_importer(a1_example, import_start_end_events=True)

    filtered_network = filter_edges(network, threshold=0)
    filtered_network = filter_events(filtered_network, threshold=0)
    filtered_network.delete_filtered_out_items()

    bpmn_network = alpha_miner(filtered_network)

    draw_simple_network(bpmn_network, with_numbers=True, auto_show=True,
                        name='BB'+str(case), title='BB'+str(case))