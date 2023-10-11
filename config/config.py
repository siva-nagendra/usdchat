import os

import yaml


class Config:
    APP_NAME = "usdchat"
    # MODEL = "gpt-4"
    MODEL = "gpt-3.5-turbo-0613"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MAX_TOKENS = 500
    TEMPERATURE = 0
    MAX_ATTEMPTS = 4
    WORKING_DIRECTORY = "/tmp"
    SYSTEM_MESSAGE = "You are a very helpful ChatBot!"
    EXAMPLE_PROMPTS = []

    @classmethod
    def load_from_yaml(cls, path):
        with open(path, "r") as file:
            config_data = yaml.safe_load(file)

        for key, value in config_data.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
        cls.SYSTEM_MESSAGE = cls.SYSTEM_MESSAGE.format(
            WORKING_DIRECTORY=cls.WORKING_DIRECTORY
        )
