import json
import os
import logging
from datetime import datetime


class ConversationManager:
    def __init__(
        self,
        new_session=False,
        config=None,
    ):
        self.config = config
        directory=f"{self.config.WORKING_DIRECTORY}/message_logs"
        self.directory = directory
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        self.session_timestamp = None
        self.session_log_filename = None
        self.file_path = None
        self.conversation = []

        if new_session:
            self.new_session()
        else:
            self.initialize_session()

    def new_session(self):
        self.session_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.session_log_filename = (
            f"message_history_session_{self.session_timestamp}.json"
        )
        self.file_path = os.path.join(self.directory, self.session_log_filename)
        with open(self.file_path, "w") as f:
            json.dump([{"role": "system", "content": self.config.SYSTEM_MESSAGE}], f)
        self.conversation = self.load()

    def initialize_session(self):
        existing_files = [f for f in os.listdir(self.directory) if f.endswith(".json")]
        if existing_files:
            sorted_files = sorted(existing_files, reverse=True)
            self.session_log_filename = sorted_files[0]
        else:
            self.new_session()

        self.file_path = os.path.join(self.directory, self.session_log_filename)
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    file_content = f.read()
                    if not file_content.strip():
                        self.conversation = [
                            {"role": "system", "content": self.config.SYSTEM_MESSAGE}
                        ]
                    else:
                        self.conversation = json.loads(file_content)
            except (UnicodeDecodeError, json.JSONDecodeError):
                logging.error(
                    "Error decoding the file. Starting with an empty conversation list."
                )
                self.conversation = []
        else:
            self.new_session()
        return self.conversation

    def save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.conversation, f, indent=2)

    def append_to_log(self, message):
        logging.info(f"Appending message: {message}")
        if not self.conversation or self.conversation[-1] != message:
            self.conversation.append(message)
            self.save()

    def insert_message(self, index, message):
        self.conversation.insert(index, message)
        self.save()

    def switch_file(self, new_file):
        self.save()
        self.file_path = os.path.join(self.directory, new_file)
        self.load()
