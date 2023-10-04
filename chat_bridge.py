import logging
from PySide6.QtCore import Signal, QObject

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatBridge(QObject):
    new_bot_response = Signal(str, str)  # signal to emit bot response

    def __init__(self, chat_bot, chat_ui):
        super().__init__()
        self.chat_bot = chat_bot  # Instance of Chat
        self.chat_ui = chat_ui  # Instance of ChatBotUI
        self.connect_signals()

    def connect_signals(self):
        self.chat_ui.submit_button.clicked.connect(self.handle_user_message)
        self.new_bot_response.connect(self.chat_ui.append_message)

    def handle_user_message(self):
        user_input = self.chat_ui.user_input.toPlainText()
        if user_input:
            try:
                bot_response = self.chat_bot.process_user_input(user_input)
                self.new_bot_response.emit(bot_response, "bot")
            except Exception as e:
                logging.error(f"Error processing user message: {e}")
                self.new_bot_response.emit("Sorry, an error occurred while processing your request.", "bot")

    def start_conversation(self):
        self.chat_ui.show()

    def stop_conversation(self):
        logging.info("Conversation ended.")
        # Add any cleanup or finalization code here if needed


# Usage:

# import the necessary classes and create instances
# from your_chat_bot_module import Chat
# from your_chat_ui_module import ChatBotUI

# chat_bot = Chat()  # Your chat bot class, initialized as needed
# chat_ui = ChatBotUI()  # Your chat UI class

# chat_bridge = ChatBridge(chat_bot, chat_ui)
# chat_bridge.start_conversation()