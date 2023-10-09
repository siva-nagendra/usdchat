import traceback
from PySide6.QtCore import QThread, Signal, QMetaObject, Qt, Q_ARG
from USDChat import chat_bridge
from utils import process_code
from USDChat.utils.conversation_manager import ConversationManager

class ChatThread(QThread):
    signal_bot_response = Signal(str)
    signal_python_exection_response = Signal(str, bool, str)

    def __init__(self, chat_bot, chat_widget, user_input, usdviewApi):
        super().__init__()
        self.stop_flag = False
        self.chat_bot = chat_bot
        self.chat_widget = chat_widget
        self.user_input = user_input
        self.all_responses = ""
        self.usdviewApi = usdviewApi
        self.conversation_manager = ConversationManager()
        self.message_history = self.conversation_manager.load()
        self.max_history = 100
        self.finished.connect(chat_bridge.ChatBridge(self.chat_bot, self.chat_widget, self.usdviewApi).clean_up_thread)

    def run(self):
        try:
            if len(self.message_history) > self.max_history:
                self.message_history = [self.message_history[0]] + self.message_history[-(self.max_history - 1) :]

            self.conversation_manager.append_message(
                {"role": "user", "content": self.user_input}
            )
            response_generator = self.chat_bot.stream_chat(self.message_history)
            
            for chunk in response_generator:
                if self.stop_flag:
                    return
                QMetaObject.invokeMethod(self.chat_widget, "append_bot_response",
                                        Qt.QueuedConnection,
                                        Q_ARG(str, chunk))

                self.all_responses += chunk
            all_responses = self.all_responses

            self.conversation_manager.append_message(
                {"role": "assistant", "content": all_responses}
            )

            if "```python" in all_responses and "```" in all_responses:
                output, success = process_code.process_chat_responses(
                    all_responses, self.usdviewApi
                )
                self.conversation_manager.append_message(
                    {"role": "assistant", "content": output}
                )
                self.signal_python_exection_response.emit(
                    output, success, all_responses)
        except Exception as e:
            print(f"An exception occurred: {e}")
            traceback.print_exc()
        
    
    def stop(self):  # Add this method
        self.stop_flag = True
