from PySide6.QtCore import Signal, QObject
from USDChat.utils.chat_thread import ChatThread


class ChatBridge(QObject):
    signal_bot_response = Signal(str)

    def __init__(self, chat_bot, chat_widget):
        super().__init__()
        self.chat_bot = chat_bot
        self.chat_widget = chat_widget
        # self.signal_bot_response.connect(self.chat_widget.update_chat_ui)

    def get_bot_response(self, user_input):
        self.chat_thread = ChatThread(self.chat_bot, user_input)
        self.chat_thread.signal_bot_response.connect(self.signal_bot_response)
        self.chat_thread.start()
