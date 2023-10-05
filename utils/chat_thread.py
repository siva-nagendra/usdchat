from PySide6.QtCore import QThread, Signal


class ChatThread(QThread):
    signal_bot_response = Signal(str)

    def __init__(self, chat_bot, user_input):
        super().__init__()
        self.chat_bot = chat_bot
        self.user_input = user_input

    def run(self):
        response_generator = self.chat_bot.stream_chat(self.user_input)
        for chunk in response_generator:
            self.signal_bot_response.emit(chunk)
