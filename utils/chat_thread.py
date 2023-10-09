from PySide6.QtCore import QThread, Signal

from utils import process_code


class ChatThread(QThread):
    signal_bot_response = Signal(str)
    signal_python_exection_response = Signal(str, bool, str)
    signal_user_message = Signal(str)

    def __init__(self, chat_bot, user_input, usdviewApi):
        super().__init__()
        self.chat_bot = chat_bot
        self.user_input = user_input
        self.all_responses = ""
        self.usdviewApi = usdviewApi

    def run(self):
        response_generator = self.chat_bot.stream_chat(self.user_input)
        for chunk in response_generator:
            self.signal_bot_response.emit(chunk)
            self.all_responses += chunk
        all_responses = self.all_responses

        if "```python" in all_responses and "```" in all_responses:
            output, success = process_code.process_chat_responses(
                all_responses, self.usdviewApi
            )
            self.signal_python_exection_response.emit(
                output, success, all_responses)
