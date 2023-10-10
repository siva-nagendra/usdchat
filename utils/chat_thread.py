from PySide6.QtCore import QThread, Signal
from usdchat import chat_bridge


class ChatThread(QThread):
    signal_bot_response = Signal(str)
    signal_bot_full_response = Signal(str)
    signal_python_code_ready = Signal(str)

    def __init__(self, chat_bot, chat_widget, messages, usdviewApi):
        super().__init__()
        self.stop_flag = False
        self.chat_bot = chat_bot
        self.chat_widget = chat_widget
        self.messages = messages
        self.all_responses = ""
        self.usdviewApi = usdviewApi
        self.finished.connect(
            chat_bridge.ChatBridge(
                self.chat_bot, self.chat_widget, self.usdviewApi
            ).clean_up_thread
        )

    def run(self):
        response_generator = self.chat_bot.stream_chat(self.messages)

        for chunk in response_generator:
            if self.stop_flag:
                return
            self.signal_bot_response.emit(chunk)
            self.all_responses += chunk

        all_responses = self.all_responses
        self.signal_bot_full_response.emit(all_responses)

        if "```python" in all_responses and "```" in all_responses:
            self.signal_python_code_ready.emit(all_responses)

    def stop(self):
        self.stop_flag = True
