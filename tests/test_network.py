import unittest

import network_factory
from network import Network, NodeType

"""
Network:
A --.             .-- E
    |-- C -- D -- |
B --^             ^-- F
"""
test_network = {
    'A': { 'C' },
    'B': { 'C' },
    'C': { 'D' },
    'D': { 'E', 'F' },
}


class NodeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.net = network_factory.from_simple_direct_succession(test_network)

    def test_is_split(self):
        # these are not splits
        self.assertFalse(self.net.nodes['A'].is_split())
        self.assertFalse(self.net.nodes['B'].is_split())
        self.assertFalse(self.net.nodes['C'].is_split())
        self.assertFalse(self.net.nodes['E'].is_split())
        self.assertFalse(self.net.nodes['F'].is_split())

        self.assertTrue(self.net.nodes['D'].is_split())

    def test_is_merge(self):
        # these are not splits
        self.assertFalse(self.net.nodes['A'].is_merge())
        self.assertFalse(self.net.nodes['B'].is_merge())
        self.assertFalse(self.net.nodes['D'].is_merge())
        self.assertFalse(self.net.nodes['E'].is_merge())
        self.assertFalse(self.net.nodes['F'].is_merge())

        self.assertTrue(self.net.nodes['C'].is_merge())

    def test_next(self):
        a = self.net.nodes['A']
        c = self.net.nodes['C']
        d = self.net.nodes['D']
        self.assertEqual(a.next().name, c.name)
        self.assertEqual(c.next().name, d.name)

    def test_prev(self):
        f = self.net.nodes['F']
        c = self.net.nodes['C']
        d = self.net.nodes['D']
        self.assertEqual(d.prev().name, c.name)
        self.assertEqual(f.prev().name, d.name)

    def test_next_throws_on_multiple_successors(self):
        d = self.net.nodes['D']
        with self.assertRaisesRegex(AssertionError, "Node .* must have only one successor .*"):
            d.next()

    def test_prev_throws_on_multiple_successors(self):
        c = self.net.nodes['C']
        with self.assertRaisesRegex(AssertionError, "Node .* must have only one predecessor .*"):
            c.prev()

    def test_prev_throws_if_no_predecessors(self):
        a = self.net.nodes['A']
        with self.assertRaises(StopIteration):
            a.prev()

    def test_remove_successor(self):
        c = self.net.nodes['C']
        d = self.net.nodes['D']

        c.remove_successor(d)

        self.assertSetEqual(c.successors, set())
        self.assertSetEqual(d.predecessors, set())

    def test_remove_predecessor(self):
        c = self.net.nodes['C']
        d = self.net.nodes['D']

        d.remove_predecessor(c)

        self.assertSetEqual(c.successors, set())
        self.assertSetEqual(d.predecessors, set())

    def test_remove_all_successors(self):
        d = self.net.nodes['D']
        e = self.net.nodes['E']
        f = self.net.nodes['F']

        d.remove_all_successors()

        self.assertSetEqual(d.successors, set())
        self.assertSetEqual(e.predecessors, set())
        self.assertSetEqual(f.predecessors, set())

    def test_remove_all_predecessors(self):
        a = self.net.nodes['A']
        b = self.net.nodes['B']
        c = self.net.nodes['C']

        c.remove_all_predecessors()

        self.assertSetEqual(a.successors, set())
        self.assertSetEqual(b.successors, set())
        self.assertSetEqual(c.predecessors, set())


class NetworkTests(unittest.TestCase):
    def test_add_node(self):
        net = Network()
        net.add_node('abc', cnt=5)

        self.assertEqual(net.nodes['abc'].name, 'abc')
        self.assertEqual(net.nodes['abc'].cnt, 5)

    def test_add_edge(self):
        net = Network()
        net.add_node('a')
        net.add_node('b')

        net.add_edge('a', 'b', 3)

        a = net.nodes['a']
        b = net.nodes['b']
        self.assertSetEqual(a.successors, {b})
        self.assertSetEqual(b.predecessors, {a})
        self.assertEqual(net.edges['a']['b'].src, a)
        self.assertEqual(net.edges['a']['b'].target, b)
        self.assertEqual(net.edges['a']['b'].cnt, 3)

    def test_delete_node(self):
        net = network_factory.from_simple_direct_succession(test_network)
        a = net.nodes['A']
        b = net.nodes['B']
        c = net.nodes['C']
        d = net.nodes['D']

        net.delete_node(c)

        self.assertDictEqual(net.edges['A'], {})
        self.assertDictEqual(net.edges['B'], {})
        self.assertNotIn('C', net.edges.keys())

        self.assertSetEqual(a.successors, set())
        self.assertSetEqual(b.successors, set())
        self.assertSetEqual(d.predecessors, set())

    def test_delete_edge(self):
        net = network_factory.from_simple_direct_succession(test_network)
        b = net.nodes['B']
        c = net.nodes['C']

        net.delete_edge(net.edges['B']['C'])

        self.assertNotIn('C', net.edges['B'].keys())
        self.assertNotIn(c, b.successors)
        self.assertNotIn(b, c.predecessors)

    def test_delete_filtered_out_items(self):
        net = network_factory.from_simple_direct_succession(test_network)
        a = net.nodes['A']
        b = net.nodes['B']
        c = net.nodes['C']
        d = net.nodes['D']
        e = net.nodes['E']

        c.is_filtered_out = True
        net.edges['D']['E'].is_filtered_out = True

        net.delete_filtered_out_items()

        self.assertDictEqual(net.edges['A'], {})
        self.assertDictEqual(net.edges['B'], {})
        self.assertNotIn('C', net.edges.keys())

        self.assertSetEqual(a.successors, set())
        self.assertSetEqual(b.successors, set())
        self.assertSetEqual(d.predecessors, set())

        self.assertNotIn(e, d.successors)
        self.assertNotIn(d, e.predecessors)
        self.assertNotIn('E', net.edges['D'].keys())

    def test_delete_node_merge_edges(self):
        # Create network a->b->c
        net = Network()
        net.add_node('a')
        net.add_node('b')
        net.add_node('c')
        net.add_edge('a', 'b')
        net.add_edge('b', 'c')

        a = net.nodes['a']
        b = net.nodes['b']
        c = net.nodes['c']

        net.delete_node_merge_edges(b)

        edge = net.edges['a']['c']
        self.assertSetEqual(a.successors, {c})
        self.assertSetEqual(c.predecessors, {a})
        self.assertIn('c', net.edges['a'].keys())
        self.assertEqual(edge.src, a)
        self.assertEqual(edge.target, c)

    def test_insert_dummy_before(self):
        net = network_factory.from_simple_direct_succession(test_network)
        c = net.nodes['C']
        original_predecessors = set(c.predecessors)

        net.insert_dummy_before(c, 'dummy1')

        self.assertIn('dummy1', net.nodes.keys())
        dummy = net.nodes['dummy1']
        self.assertEqual(dummy.type, NodeType.DUMMY)
        self.assertSetEqual(dummy.predecessors, original_predecessors)
        self.assertSetEqual(dummy.successors, {c})
        self.assertSetEqual(c.predecessors, {dummy})

        # validate edges - im too lazy to write assertions
        net._validate_structure()

    def test_insert_dummy_after(self):
        net = network_factory.from_simple_direct_succession(test_network)
        d = net.nodes['D']
        original_successors = set(d.successors)

        net.insert_dummy_after(d, 'dummy1')

        self.assertIn('dummy1', net.nodes.keys())
        dummy = net.nodes['dummy1']
        self.assertEqual(dummy.type, NodeType.DUMMY)
        self.assertSetEqual(dummy.successors, original_successors)
        self.assertSetEqual(dummy.predecessors, {d})
        self.assertSetEqual(d.successors, {dummy})

        # validate edges - im too lazy to write assertions
        net._validate_structure()
