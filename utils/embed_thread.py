import logging

from PySide6.QtCore import QThread, Signal

from usdchat.services.chromadb_collections import ChromaDBCollections
from utils.resolve_stage_layers import resolve_all_layers


class EmbedThread(QThread):
    signal_embed_complete = Signal(int)
    signal_progress_update = Signal(int, str)

    def __init__(self, stage_path, collection_name, config=None):
        super().__init__()
        self.stage_path = stage_path
        self.collection_name = collection_name
        self.config = config
        print(f"EmbedThread Config: {self.config}")
        self.chromadb_collections = ChromaDBCollections(config=self.config)

    def run(self):
        final_paths = resolve_all_layers(
            self.stage_path, self.signal_progress_update)

        self.chromadb_collections.reset_chromadb()

        chunks = self.chromadb_collections.create_and_store_embeddings(
            files=final_paths,
            collection_name=self.collection_name,
            signal_progress_update=self.signal_progress_update,
        )

        if chunks:
            self.signal_embed_complete.emit(len(chunks))
        else:
            logging.error("No chunks embedded.")
            self.signal_embed_complete.emit(0)

    def stop(self):
        self.terminate()
        self.wait()
