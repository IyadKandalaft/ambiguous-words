# -*- coding: utf-8 -*-

class Graph:
    def __init__(self):
        self.nodes = {}

    def __getitem__(self, v):
        if v in self.nodes:
            return self.nodes[v]
        
        return None

    def __len__(self):
        return len(self.nodes)
        
    def add_node(self, name):
        if name in self.nodes:
            return self.nodes[name]

        self.nodes[name] = Node(name)

        return self.nodes[name]

    def add_edge(self, name_u, name_v):
        u = self.nodes[name_u]
        v = self.nodes[name_v]
        u.neighbors[name_v] = v
        v.neighbors[name_u] = u

    def delete_node(self, name):
        if name in self.nodes:
            del self.nodes[name]

    def clear(self):
        self.nodes.clear()

class Node:
    """A node element within a graph
    """
    def __init__(self, value):
        self.neighbors = {}
        self.value = value

    