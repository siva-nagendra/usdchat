from PySide6.QtCore import Signal, QObject

class ChatBridge(QObject):
    signal_bot_response = Signal(str)
    def __init__(self, chat_bot, chat_widget):
        super().__init__()
        self.chat_bot = chat_bot
        self.chat_widget = chat_widget
        # self.signal_bot_response.connect(self.chat_widget.update_chat_ui)

    def get_bot_response(self, user_input):
        print(f"User input: {user_input}")
        bot_response = self.chat_bot.chat(user_input)
        print(f"Bot response: {bot_response}")
        self.signal_bot_response.emit(bot_response)
