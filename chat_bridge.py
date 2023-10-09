from PySide6.QtCore import QObject, Signal

from USDChat.utils.chat_thread import ChatThread


class ChatBridge(QObject):
    signal_bot_response = Signal(str)

    def __init__(self, chat_bot, chat_widget, usdviewApi):
        super().__init__()
        self.chat_bot = chat_bot
        self.chat_widget = chat_widget
        self.usdviewApi = usdviewApi
        self.chat_threads = []

    def get_bot_response(self, user_input):
        chat_thread = ChatThread(self.chat_bot, user_input, self.usdviewApi)
        self.chat_threads.append(
            chat_thread
        )  # Keep a reference to prevent garbage collection
        chat_thread.signal_bot_response.connect(self.signal_bot_response)
        chat_thread.signal_python_exection_response.connect(
            self.chat_widget.append_python_output
        )  # Add this line
        chat_thread.start()
