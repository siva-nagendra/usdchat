import json
import os
import time
from datetime import datetime

import openai

from USDChat.config import Config

openai.api_key = Config.OPENAI_API_KEY


class Chat:
    def __init__(self, model):
        self.model = model
        self.system = Config.SYSTEM_MESSAGE
        self.max_tokens = Config.MAX_TOKENS
        self.temp = Config.TEMP
        self.max_history = 100
        self.message_history = [{"role": "system", "content": self.system}]
        self.session_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.session_log_filename = (
            f"message_history_session_{self.session_timestamp}.json"
        )
        self.full_message_history = []

    def append_to_session_log(self, messages):
        self.full_message_history.extend(messages)
        if len(self.full_message_history) > self.max_history:
            self.full_message_history = self.full_message_history[-self.max_history:]

    def save_session_log(self, directory="./message_logs"):
        if not os.path.exists(directory):
            os.makedirs(directory)
        file_path = os.path.join(directory, self.session_log_filename)
        with open(file_path, "w") as outfile:
            json.dump(self.full_message_history, outfile, indent=2)

    def stream_chat(self, messages, delay_time=0.1):
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        # Insert system message if not present
        if len(messages) == 0 or (
            len(messages) > 0 and messages[0].get("role") != "system"
        ):
            messages.insert(0, {"role": "system", "content": self.system})
        local_message_history = []
        response = openai.ChatCompletion.create(
            model=self.model,
            temperature=self.temp,
            max_tokens=self.max_tokens,
            messages=messages,
            stream=True,
        )
        reply_content = ""
        for event in response:
            event_text = event["choices"][0]["delta"]
            new_text = event_text.get("content", "")
            reply_content += new_text
            local_message_history.append(
                {"role": "assistant", "content": new_text})
            if len(self.message_history) > self.max_history:
                self.message_history = self.message_history[-self.max_history:]

            yield new_text

            time.sleep(delay_time)

        self.append_to_session_log(local_message_history)
        return reply_content
