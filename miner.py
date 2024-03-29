from copy import deepcopy

from bpmn_network import NodeKind, BPMNNetwork, UtilityNode, NodeFunction
from network import NodeType, Edge


def patch_gate_to_gate(net: BPMNNetwork):
    '''
        pseudokod brama brama:

        predecessors_of_my_successors = set()
        for successor in self.successors:
            predecessors_of_my_successors.update(successor.predecessors)

        if successor.predecessors == predecessors_of_my_successors forall successor in self.successors:
            merge(predecessors_of_my_successors, temp)
            split(temp, self.successors)
        '''
    causality = net.get_causality()
    processed_nodes = set()
    for node, succs in causality.items():
        if node in processed_nodes or len(succs) <= 1:
            continue
        for _n, _s in causality.items():
            if _n in processed_nodes:
                break
            if _n != node and _s == succs:
                s = set(_s)

                predecessors_of_my_successors = {_n, node}
                tmp = net.add_node(f'tmp_g2g_{_n.name}')
                #tmp.type = NodeType.DUMMY
                tmp.successors = set(s)
                tmp.predecessors = set(predecessors_of_my_successors)
                for p in predecessors_of_my_successors:
                    net.edges[p.name] = {tmp.name: Edge(net, p, tmp)}
                    p.successors = {tmp}
                net.edges[tmp.name] = {}
                for succ in s:
                    net.edges[tmp.name][succ.name] = Edge(net, tmp, succ)
                    succ.predecessors.remove(_n)
                    succ.predecessors.remove(node)
                    succ.predecessors.add(tmp)

                kind = NodeKind.AND if net.are_all_nodes_parallel(predecessors_of_my_successors) else NodeKind.XOR
                #net.insert_merge_node_between(predecessors_of_my_successors, tmp, kind)

                #kind = NodeKind.AND if net.are_all_nodes_parallel(s) else NodeKind.XOR
                #net.insert_split_node_between(tmp, s, kind)

                #net.delete_node_merge_edges(tmp)
                processed_nodes.update(predecessors_of_my_successors)
                break


def alpha_miner(network: BPMNNetwork) -> BPMNNetwork:
    """
    Alpha miner taki sam jak u nas w Lab 2
    Ale to jest jego wersja, tzn nie ma JESZCZE obsługi 2 bram bezpośrednio po sobie

    :return: Zwraca nowa siec z bramami
    """
    net = deepcopy(network)
    patch_gate_to_gate(net)
    net.process_short_loops()

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
            evt = event
            if event.is_merge():
                evt = net.insert_dummy_after(event, f'dummy_after_{event.name}')
            if net.are_all_nodes_parallel(successions):
                parallelisms += [successions]
                net.delete_parallelism_from_all(successions)
                net.insert_split_node_between(evt, successions, kind=NodeKind.AND)
            else:
                net.insert_split_node_between(evt, successions, kind=NodeKind.XOR)

    # Drugi for do niego
    # nie uzywam inv_causality bo mam swoje narzedzia od tego
    for node in set(net.nodes.values()):
        if not node.is_merge() or (isinstance(node, UtilityNode) and node.function == NodeFunction.LOOP_GATE):
            continue

        prevs = set(node.predecessors)  # we need to copy
        if prevs in parallelisms:
            net.insert_merge_node_between(prevs, node, kind=NodeKind.AND)
        else:
            net.insert_merge_node_between(prevs, node, kind=NodeKind.XOR)

    dummies = set(d for d in net.nodes.values() if d.type == NodeType.DUMMY or d.name.startswith('tmp_g2g_'))
    for d in dummies:
        net.delete_node_merge_edges(d)

    update_end_events(net, parallelisms)
    update_start_events(net, parallelisms)

    return net


def update_start_events(net: BPMNNetwork, parallelisms=None):
    if parallelisms is None:
        parallelisms = []
    start_events = net.get_start_events()

    # Only one start event, nothing to do
    if len(start_events) <= 1:
        return

    gate = UtilityNode(net, name='start_split_gate')
    gate.function = NodeFunction.SPLIT
    gate.kind = NodeKind.AND if start_events in parallelisms else NodeKind.XOR
    gate.is_start_node = True
    net.nodes['start_split_gate'] = gate

    for ev in start_events:
        ev.is_start_node = False  # they're no longer starting events
        ev.remove_all_predecessors()
        net.add_edge(gate.name, ev.name, ev.cnt)


def update_end_events(net: BPMNNetwork, parallelisms=None):
    if parallelisms is None:
        parallelisms = []
    end_events = net.get_end_events()

    # Only one end event, nothing to do
    if len(end_events) <= 1:
        return

    gate = UtilityNode(net, name='end_merge_gate')
    gate.function = NodeFunction.MERGE
    gate.kind = NodeKind.AND if end_events in parallelisms else NodeKind.XOR
    gate.is_end_node = True
    net.nodes[gate.name] = gate

    for ev in end_events:
        ev.is_end_node = False  # they're no longer end events
        ev.remove_all_successors()
        # ev.cnt is not really correct
        net.add_edge(ev.name, gate.name, ev.cnt)
