import json
import os
from datetime import datetime
from USDChat.config import Config

class ConversationManager:
    def __init__(self, default_file="default_conversation.json", directory=f"{Config.WORKING_DIRECTORY}/message_logs"):
        self.directory = directory
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        
        self.session_timestamp = None
        self.session_log_filename = None
        self.file_path = None
        self.conversation = []

        self.initialize_session()

    def initialize_session(self):
        print(f"Initializing in directory: {self.directory}")  # Debug print
        existing_files = [f for f in os.listdir(self.directory) if f.endswith('.json')]
        if existing_files:
            sorted_files = sorted(existing_files, reverse=True)
            self.session_log_filename = sorted_files[0]
        else:
            self.session_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.session_log_filename = f"message_history_session_{self.session_timestamp}.json"
            print(f"Creating new file: {self.session_log_filename}")  # Debug print
            with open(os.path.join(self.directory, self.session_log_filename), 'w') as f:
                json.dump([], f)

        self.file_path = os.path.join(self.directory, self.session_log_filename)
        self.load()


    def load(self):
        print(f"Loading from file: {self.file_path}")  # Debug print
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    self.conversation = json.load(f)
            except UnicodeDecodeError:
                print("Error decoding the file. Starting with an empty conversation list.")
                self.conversation = []
        else:
            print(f"File not found. Creating and initializing: {self.file_path}")  # Debug print
            with open(self.file_path, 'w') as f:
                json.dump([], f)
            self.conversation = []
        return self.conversation


    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.conversation, f, indent=2)  # Using indent=2 as in your example

    def append_message(self, message):
        self.conversation.append(message)
        self.save()

    def switch_file(self, new_file):
        self.save()
        self.file_path = os.path.join(self.directory, new_file)
        self.load()
