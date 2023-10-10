import logging
from PySide6.QtCore import QObject, Signal
from usdchat.utils.chat_thread import ChatThread
from usdchat.utils.conversation_manager import ConversationManager
from usdchat.config import Config


class ChatBridge(QObject):
    signal_bot_response = Signal(str)
    signal_python_code_ready = Signal(str)

    def __init__(self, chat_bot, chat_widget, usdviewApi, conversation_manager=None):
        super().__init__()
        self.chat_bot = chat_bot
        self.chat_widget = chat_widget
        self.usdviewApi = usdviewApi
        self.chat_threads = []
        self.conversation_manager = (
            conversation_manager if conversation_manager else ConversationManager()
        )

    @property
    def conversation_manager(self):
        return self._conversation_manager

    @conversation_manager.setter
    def conversation_manager(self, new_manager):
        self._conversation_manager = new_manager

    def get_bot_response(self, user_input):
        if user_input == "clear":
            self.clear_chat_ui()
            self.chat_bridge = ChatBridge(self.chat_bot, self, self.usdviewApi)
            return
        elif user_input == "new session":
            self.conversation_manager.new_session()

        messages = self.get_messages()

        self.conversation_manager.append_to_log({"role": "user", "content": user_input})

        chat_thread = ChatThread(
            self.chat_bot, self.chat_widget, messages, self.usdviewApi
        )

        self.chat_threads.append(chat_thread)

        chat_thread.signal_bot_response.connect(self.signal_bot_response)
        chat_thread.signal_bot_full_response.connect(self.on_bot_full_response)

        chat_thread.signal_python_code_ready.connect(self.signal_python_code_ready)

        self.chat_widget.signal_python_execution_response.connect(
            self.on_python_execution_response
        )

        chat_thread.start()

    def get_messages(self):
        messages = self.conversation_manager.load()
        return messages

    def on_python_execution_response(self, python_output, success):
        self.conversation_manager.append_to_log(
            {
                "role": "assistant",
                "content": f"python_output: {python_output}, success: {success}",
            }
        )

    def on_bot_full_response(self, response):
        logging.info("on_bot_full_response", response)
        self.conversation_manager.append_to_log(
            {"role": "assistant", "content": response}
        )
        self.chat_widget.enable_send_button()

    def clean_up_thread(self):
        if self.chat_threads:
            last_thread = self.chat_threads[-1]
            last_thread.stop()
            last_thread.quit()
            last_thread.wait()
            self.chat_threads.remove(last_thread)
