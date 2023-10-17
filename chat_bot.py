import logging
import time
import traceback
from typing import List

import chromadb
import chromadb.utils.embedding_functions as ef
import openai

from config.config import Config
from usdchat.error_handlers.openai_error_handler import handle_openai_error
from usdchat.utils.embed_usda import get_or_create_collection

openai.api_key = Config.OPENAI_API_KEY

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class ChromaDBQueryAgent:
    def __init__(self, config=None):
        self.config = config
        self.client = chromadb.PersistentClient(path=self.config.DB_PATH)
        self.embedding_function = ef.SentenceTransformerEmbeddingFunction(
            self.config.EMBEDDING_MODEL
        )
        self.collection = get_or_create_collection(self.client, "stage")

    def query_embeddings(
        self, query_texts: List[str], n_results: int = 10
    ) -> chromadb.api.types.QueryResult:
        query_embeds = self.embedding_function(query_texts)
        results = self.collection.query(
            query_embeddings=query_embeds,
            n_results=n_results,
            include=["documents"])
        return results

    def query_agent(self, query_text: str, n_results: int = 10):
        query_results = self.query_embeddings([query_text], n_results)
        flat_list = [item for sublist in query_results["documents"]
                     for item in sublist]
        context = " ".join(flat_list)
        logging.info(f"Context: {context}")
        return context


class Chat:
    def __init__(self, model, config=None, rag_mode=None):
        self.model = model
        self.config = config
        self.rag_mode = rag_mode
        self.max_tokens = self.config.MAX_TOKENS
        self.temperature = self.config.TEMPERATURE
        self.query_agent = ChromaDBQueryAgent(config=self.config)
        self.context = None

    def get_embeddings(self, texts: List[str]):
        print(f"Getting embeddings for texts: {texts}")
        return self.query_agent.query_embeddings(texts)

    def query(self, query_text: str, n_results: int = 10):
        return self.query_agent.query_agent(query_text, n_results)

    def stream_chat(self, messages, delay_time=0.1):
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        self.query_text = messages[-1]["content"]
        self.context = self.query(self.query_text)

        prompt = [
            {
                "role": "system",
                "content": self.config.RAG_PROMPT,
            },
            {"role": "user", "content": f"{self.query_text} {self.context}"},
        ]
        messages.extend(prompt)
        print(f"Messages: {messages}")
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                temperature=self.temperature,
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
            logging.error(f"OpenAI API Error: {error_message}")
        except openai.error.APIConnectionError as e:
            logging.error("Failed to connect to OpenAI API.")
        except openai.error.RateLimitError as e:
            logging.error("OpenAI API request exceeded rate limit.")
        except openai.error.Timeout as e:
            logging.error("Request to OpenAI API timed out.")
        except Exception as e:
            logging.error(f"An exception occurred: {e}")
            traceback.print_exc()
