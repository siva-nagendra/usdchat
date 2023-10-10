import time
import openai
from USDChat.config import Config
from USDChat.error_handlers.openai_error_handler import handle_openai_error
import traceback

openai.api_key = Config.OPENAI_API_KEY


class Chat:
    def __init__(self, model):
        self.model = model
        self.system = Config.SYSTEM_MESSAGE
        self.max_tokens = Config.MAX_TOKENS
        self.temp = Config.TEMP
        # self.max_history = 100
        self.full_message_history = []

    def stream_chat(self, messages, delay_time=0.1):
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        try:
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
        except openai.error.APIError as e:
            error_message = handle_openai_error(401)
            print(f"OpenAI API Error: {error_message}")
        except openai.error.APIConnectionError as e:
            print("Failed to connect to OpenAI API.")
        except openai.error.RateLimitError as e:
            print("OpenAI API request exceeded rate limit.")
        except openai.error.Timeout as e:
            print("Request to OpenAI API timed out.")
        except Exception as e:
            print(f"An exception occurred: {e}")
            traceback.print_exc()
