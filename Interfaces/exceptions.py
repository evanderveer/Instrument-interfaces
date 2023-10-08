class InstrumentError(Exception):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"InstrumentError: {super().__str__()}"