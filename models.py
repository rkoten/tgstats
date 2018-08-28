class TgChat:
    def __init__(self, name):
        self.name = name
        self.messages = []
        self.n_outgoing = 0

    def add_message(self, message):
        self.messages.append(message)
        if message.is_outgoing:
            self.n_outgoing += 1


class TgMessage:
    def __init__(self, is_outgoing):
        self.is_outgoing = is_outgoing