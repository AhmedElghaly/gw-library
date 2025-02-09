class GatewayError(Exception):
    def __init__(self, *args):
        super().__init__()
        self.msg = "Gateway Error"
        if args:
            self.msg += ": " + str(args[0])

    def get_error_msg(self):
        return self.msg
