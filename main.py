import examples
import matplotlib.pyplot as plt

if __name__ == '__main__':
    print('Hello')

    examples.lab1_repair_example()
    examples.lab2_example()
    examples.lab2_ex1()
    examples.lab2_ex2()

    plt.show()

    #
    #
    # repair_example = from_csv('data/repairExample.csv')
    #
    # network = network_factory.from_counter_direct_succession(repair_example.direct_succession, repair_example.event_counter)
    # # network = from_simple_direct_succession(direct_succession)
    #
    # filtered_network = filter_edges(network, threshold=400)
    # filtered_network = filter_events(filtered_network, threshold=700)
    # filtered_network.delete_filtered_out_items()
    #
    # pprint(filtered_network.get_causality())
    #
    # for n in filtered_network.autodetect_start_nodes():
    #     print('Found start node:', n)
    #
    # for n in filtered_network.autodetect_end_nodes():
    #     print('Found end node:', n)
    #
    # draw_simple_network(filtered_network, ortho=False, with_numbers=True, auto_show=True)
    #