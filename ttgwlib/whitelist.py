from ttgwlib.node import Node

class Whitelist:
    """A class representing a whitelist of nodes."""

    def __init__(self, gateway):
        """
        Constructor for Whitelist.
        """
        self.gw = gateway
        self.whitelist = []

    def add_node(self, node):
        """
        Add a node to the whitelist.
        """
        if not isinstance(node, Node):
            return False
        if node in self.whitelist:
            return True
        self.whitelist.append(node)
        return True

    def remove_node(self, node):
        """
        Remove a node from the whitelist.
        """
        if not isinstance(node, Node):
            return False
        if node not in self.whitelist:
            return False
        if self.gw.models.task_queue.node_is_in_queue(node):
            self.gw.models.task_queue.node_cancel_tasks(node)
        self.whitelist.remove(node)
        return True

    def is_node_in_whitelist(self, node):
        """
        Check if a node is in the whitelist.
        """
        if not isinstance(node, Node):
            return False
        return node in self.whitelist

    def get_nodes(self):
        """
        Get the list of nodes in the whitelist.
        """
        return self.whitelist
