import os

import yaml

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["ALLOW_RESET"] = "TRUE"


class Config:
    APP_NAME = "usdchat"
    # MODEL = "gpt-4"
    MODEL = "gpt-3.5-turbo-0613"
    DB_PATH = "/tmp/chromadb.db"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    TOKENIZER_MODEL = "gpt-3.5-turbo-0613"
    MAX_EMBEDDING_TOKENS = 2000
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MAX_TOKENS = 500
    TEMPERATURE = 0
    MAX_ATTEMPTS = 4
    WORKING_DIRECTORY = "/tmp"
    SYSTEM_MESSAGE = "You are a very helpful ChatBot!"
    RAG_PROMPT = "You answer a user's question, given OpenUSD stage usda files as context to help\
                answer the question. The context given is from the ChromaDB database, \
                which contains pre-embedded texts. Do not contradict the contents of the given text in your answer."
    EXAMPLE_PROMPTS = []
    COLLECTION_NAME = "usdchat"

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
