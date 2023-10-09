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
        self.full_message_history = []

    def stream_chat(self, messages, delay_time=0.1):
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        if len(messages) == 0 or (
            len(messages) > 0 and messages[0].get("role") != "system"
        ):
            messages.insert(0, {"role": "system", "content": self.system})
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
            yield new_text

            time.sleep(delay_time)

        return reply_content
