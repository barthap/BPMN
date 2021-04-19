import unittest

import network_factory
from network import Network, NodeType

"""
Network:
X --> Y --> Z
     | ^
     v |
      A
    
logs:
x y z
x y a y z
"""
test_net_short_loop1 = {
    'X': { 'Y' },
    'Y': { 'A', 'Z' },
    'A': { 'Y' },
}


"""
> X--------> Y 
  |          ^
  L--> A ----|
  
logs:
x y
x a y
"""
# logs =
test_net_short_loop2 = {
    'X': { 'A', 'Y' },
    'A': { 'A', 'Y' }
}


class NodeTests(unittest.TestCase):
    pass
