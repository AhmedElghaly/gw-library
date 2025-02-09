import logging


logger = logging.getLogger(__name__)


class ReplayCache:
    def __init__(self):
        self.cache = {}

    def remove_node(self, node_address):
        if node_address in self.cache:
            del self.cache[node_address]

    def check_seq_number(self, node_address, seq_number):
        if node_address in self.cache:
            if seq_number > self.cache[node_address]:
                self.cache[node_address] = seq_number
                return True
            logger.log(9, f"Replay cache repeated: {node_address=}, " +
                         f"{seq_number=}, {self.cache[node_address]=}")
            return False

        self.cache[node_address] = seq_number
        return True
