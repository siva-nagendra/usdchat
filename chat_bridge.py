import logging

from PySide6.QtCore import QObject, Signal

from usdchat.services.chromadb_collections import ChromaDBCollections
from usdchat.utils import chat_thread, embed_thread

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ChatBridge(QObject):
    signal_bot_response = Signal(str)
    signal_python_code_ready = Signal(str)
    signal_progress_update = Signal(int, str)
    signal_embed_complete = Signal(int)

    def __init__(
        self,
        chat_bot,
        chat_widget,
        usdviewApi=None,
        config=None,
        conversation_manager=None,
        standalone=False,
        collection_name="",
        rag_mode=None,
    ):
        super().__init__()
        self.chat_bot = chat_bot
        self.chat_widget = chat_widget
        self.standalone = standalone
        self.usdviewApi = usdviewApi
        self.config = config
        self.rag_mode = rag_mode
        self.chat_thread_instance = chat_thread
        self.chat_threads = []
        self.embed_thread_instance = embed_thread
        self.embed_threads = []
        self.conversation_manager = conversation_manager
        self.chromadb_collections = ChromaDBCollections(config=self.config)
        self.collection_name = collection_name

    @property
    def conversation_manager(self):
        return self._conversation_manager

    @conversation_manager.setter
    def conversation_manager(self, new_manager):
        self._conversation_manager = new_manager

    def get_bot_response(self, user_input):
        if user_input == "clear":
            self.clear_chat_ui()
            self.chat_bridge = ChatBridge(self.chat_bot, self, self.usdviewApi)
            return
        elif user_input == "new session":
            self.conversation_manager.new_session()

        messages = self.get_messages()
        self.conversation_manager.append_to_log(
            {"role": "user", "content": user_input})

        if self.rag_mode:
            messages = self.get_query_messages(user_input, messages)

        self.chat_thread = self.chat_thread_instance.ChatThread(
            self.chat_bot,
            self.chat_widget,
            messages,
            self.usdviewApi,
            config=self.config,
        )
        self.chat_threads.append(self.chat_thread)
        self.chat_thread.start()

        self.chat_thread.signal_bot_response.connect(self.signal_bot_response)
        self.chat_thread.signal_bot_full_response.connect(
            self.on_bot_full_response)

        self.chat_widget.signal_python_execution_response.connect(
            self.on_python_execution_response
        )

    def get_messages(self):
        messages = self.conversation_manager.load()
        return messages

    def get_query_messages(self, user_input, messages):
        self.query_text = user_input
        self.context = self.query_agent(self.query_text)

        prompt = [
            {
                "role": "system",
                "content": self.config.RAG_PROMPT,
            },
            {"role": "user", "content": f"{self.query_text} {self.context}"},
        ]
        messages.extend(prompt)

        return messages

    def query_agent(self, query_text, n_results=5):
        query_results = self.chromadb_collections.query_collection(
            collection_name=self.collection_name,
            query_texts=[query_text],
            n_results=n_results,
            include=["documents"],
        )
        flat_list = [item for sublist in query_results["documents"]
                     for item in sublist]
        context = " ".join(flat_list)
        logger.info(f"Context: {context}")
        return context

    def on_python_execution_response(self, python_output, success):
        self.conversation_manager.append_to_log(
            {
                "role": "assistant",
                "content": f"python_output: {python_output}, success: {success}",
            }
        )

    def on_bot_full_response(self, response):
        logger.info("on_bot_full_response: %s", response)

        if not self.standalone:
            if "```python" in response and "```" in response:
                self.signal_python_code_ready.emit(response)

        self.conversation_manager.append_to_log(
            {"role": "assistant", "content": response}
        )
        self.chat_widget.enable_send_button()

    def embed_stage(self, stage_path):
        self.embed_thread = self.embed_thread_instance.EmbedThread(
            stage_path, collection_name=self.collection_name, config=self.config)
        self.embed_threads.append(self.embed_thread)
        self.embed_thread.start()

        self.embed_thread.signal_progress_update.connect(
            self.signal_progress_update)
        self.embed_thread.signal_embed_complete.connect(self.on_embed_complete)

    def on_embed_complete(self, no_of_chunks):
        logger.info(f"Embedding complete. {no_of_chunks} files embedded.")
        self.clean_up_thread()
        self.signal_embed_complete.emit(no_of_chunks)

    def clean_up_thread(self):
        if self.chat_threads:
            last_thread = self.chat_threads[-1]
            last_thread.stop()
            last_thread.quit()
            last_thread.wait()
            self.chat_threads.remove(last_thread)

        if self.embed_threads:
            last_thread = self.embed_threads[-1]
            last_thread.stop()
            last_thread.quit()
            last_thread.wait()
            self.embed_threads.remove(last_thread)
