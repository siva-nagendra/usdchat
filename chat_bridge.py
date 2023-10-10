from PySide6.QtCore import QObject, Signal
from USDChat.utils.chat_thread import ChatThread
from USDChat.utils.conversation_manager import ConversationManager
from USDChat.config import Config


class ChatBridge(QObject):
    signal_bot_response = Signal(str)
    signal_python_code_ready = Signal(str)

    def __init__(self, chat_bot, chat_widget, usdviewApi):
        super().__init__()
        self.chat_bot = chat_bot
        self.chat_widget = chat_widget
        self.usdviewApi = usdviewApi
        self.chat_threads = []
        self.conversation_manager = ConversationManager()
        self.max_attempts = Config.MAX_ATTEMPTS
        self.current_attempts = 0

    def get_bot_response(self, user_input):
        if user_input == "clear":
            self.chat_widget.clear_chat_ui()
            return
        elif user_input == "new session":
            self.conversation_manager.new_session()

        messages = self.get_messages()

        self.conversation_manager.append_message(
            {"role": "user", "content": user_input}
        )

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
        if len(messages) == 0 or (
            len(messages) > 0 and messages[0].get("role") != "system"
        ):
            self.conversation_manager.insert_message(
                0, {"role": "system", "content": Config.SYSTEM_MESSAGE}
            )
        return messages

    def on_python_execution_response(self, python_output, success):
        if success:
            self.current_attempts = 0
            self.chat_widget.enable_send_button()
        else:
            self.current_attempts += 1
        print("on_python_execution_response", python_output, success)

        if self.current_attempts >= self.max_attempts:
            self.current_attempts = 0  # Reset counter
            self.signal_user_message.emit("stop")
            self.chat_widget.enable_send_button()
        self.conversation_manager.append_message(
            {
                "role": "assistant",
                "content": f"python_output: {python_output}, success: {success}",
            }
        )

    def on_bot_full_response(self, response):
        print("on_bot_full_response", response)
        self.conversation_manager.append_message(
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
