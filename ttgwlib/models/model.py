class Model:
    def __init__(self, gateway, handlers):
        self.gw = gateway
        for handler in handlers:
            gateway.add_event_handler(handler)

    def add_task(self, task):
        self.gw.models.task_queue.add_task(task)

    def cancel_tasks(self, node):
        self.gw.models.task_queue.cancel_tasks(node)

    def reschedule_tasks(self, node):
        self.gw.models.task_queue.reschedule_tasks(node)

    def send(self, data, node):
        self.gw.tx_manager.send_node(data, node)

    def send_addr(self, data, addr, low_priority=False):
        self.gw.tx_manager.send_addr(data, addr, low_priority)

    @classmethod
    def opcode_to_bytes(cls, opcode, company_id=None):
        b = bytearray([])
        if company_id is not None:
            b += opcode.to_bytes(1, "big")
            b += company_id.to_bytes(2, "little")
        elif opcode > 0x00FF:
            b += opcode.to_bytes(2, "big")
        else:
            b += opcode.to_bytes(1, "big")
        return b
