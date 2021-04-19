import unittest

import network_factory
from network import Network, NodeType


"""
Picture 1 (Self loop)
X ----> A --> Y
     ^  |
     L--+
     
logs
x a y
x a a y
x a a a y
"""
test_net_loop1 = {
    'X': {'A'},
    'A': {'A', 'Y'}
}

"""
Picture 2
> X--------> Y 
  |          ^
  L--> A ----|

logs:
x y
x a y
x a a y
"""
test_net_loop2 = {
    'X': {'A', 'Y'},
    'A': {'A', 'Y'}
}

"""
Network (picture 3):
X --> A --> Y
     | ^
     v |
      B
    
logs:
x a y
x a b a y
x a b a b a y
"""
test_net_loop3 = {
    'X': { 'A' },
    'A': { 'B', 'Y' },
    'B': { 'A' },
}


class NodeTests(unittest.TestCase):
    def test_self_loop(self):
        net = network_factory.from_simple_direct_succession(test_net_loop1)
        a = net.nodes['A']
        self.assertTrue(a.is_self_loop())

    def test_short_loop(self):
        net = network_factory.from_simple_direct_succession(test_net_loop2)
        a = net.nodes['A']
        self.assertTrue(a.is_short_loop())

    def test_two_loop(self):
        net = network_factory.from_simple_direct_succession(test_net_loop3)
        a = net.nodes['A']
        b = net.nodes['B']
        self.assertTrue(b.is_two_loop())
        self.assertFalse(a.is_two_loop())
