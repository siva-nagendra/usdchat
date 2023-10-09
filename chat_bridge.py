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
        if user_input == "clear":
            self.chat_widget.clear_chat_ui()
            return

        chat_thread = ChatThread(self.chat_bot, self.chat_widget, user_input, self.usdviewApi)
        self.chat_threads.append(
            chat_thread
        ) 
        chat_thread.signal_bot_response.connect(self.signal_bot_response)
        chat_thread.signal_python_exection_response.connect(
            self.chat_widget.append_python_output
        )
        chat_thread.start()

    
    def clean_up_thread(self):
        if self.chat_threads:
            last_thread = self.chat_threads[-1]
            last_thread.stop()
            last_thread.quit()
            last_thread.wait()
