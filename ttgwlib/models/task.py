class Task:
    MAX_RETRIES = 4
    def __init__(self, node, success_events, error_events):
        self.node = node
        self.success_events = success_events
        self.error_events = error_events

    def handler(self, event):
        if event.event_type in self.success_events:
            self.success(event)
            return True
        if event.event_type in self.error_events:
            self.error(event)
        return False

    def execute(self):
        raise NotImplementedError

    def success(self, event):
        raise NotImplementedError

    def error(self, event):
        raise NotImplementedError

    def __str__(self):
        return self.__class__.__name__[:-4]

    def __repr__(self):
        return str(self)
