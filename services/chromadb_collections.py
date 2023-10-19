import logging

import chromadb
import chromadb.utils.embedding_functions as ef

from utils.chunk_ascii_files import split_files_to_chunks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ChromaDBCollections:
    def __init__(self, config=None):
        self.config = config
        self.client = chromadb.PersistentClient(path=self.config.DB_PATH)
        self.embedding_function = ef.SentenceTransformerEmbeddingFunction(
            self.config.EMBEDDING_MODEL
        )

    def create_collection(
            self,
            name,
            embedding_function=None,
            distance_metric="l2"):
        metadata = {"hnsw:space": distance_metric}
        collection = self.client.create_collection(
            name=name, embedding_function=embedding_function, metadata=metadata
        )
        return collection

    def get_collection(self, name, embedding_function=None):
        return self.client.get_collection(
            name=name, embedding_function=embedding_function
        )

    def get_or_create_collection(self, name, embedding_function=None):
        return self.client.get_or_create_collection(
            name=name, embedding_function=embedding_function
        )

    def create_and_store_embeddings(
        self,
        files,
        collection_name,
        signal_progress_update=None,
        progress_range=(60, 100),
    ):
        collection = self.get_or_create_collection(
            collection_name, embedding_function=self.embedding_function
        )
        chunks = split_files_to_chunks(files)
        total_chunks = len(chunks)
        logger.info(f"Found {total_chunks} chunks.")

        batch_size = 80000
        for i in range(0, total_chunks, batch_size):
            batch_docs = chunks[i: i + batch_size]
            batch_ids = [f"doc_{j}" for j in range(i, i + len(batch_docs))]

            # Report progress
            if signal_progress_update:
                progress = progress_range[0] + (
                    ((i + len(batch_docs)) / total_chunks) * (progress_range[1] - 80)
                )
                signal_progress_update.emit(
                    int(progress),
                    f"Adding to {collection_name} collections: {i + len(batch_docs)}/{total_chunks} chunks ({int(progress)}%)",
                )

            try:
                collection.add(documents=batch_docs, ids=batch_ids)
            except EOFError as e:
                logger.error(f"Error adding documents to collection: {e}")
                self.client.delete_collection(collection_name)
                collection = self.get_or_create_collection(
                    self.client, collection_name)
                collection.add(documents=batch_docs, ids=batch_ids)

            if signal_progress_update:
                progress = progress_range[0] + (
                    ((i + len(batch_docs)) / total_chunks) * (progress_range[1] - 80)
                )
                signal_progress_update.emit(
                    int(progress),
                    f"Embedding: {i + len(batch_docs)}/{total_chunks} chunks ({int(progress)}%)",
                )

        logger.info(f"Upserted {total_chunks} chunks.")
        if signal_progress_update:
            signal_progress_update.emit(
                progress_range[1], f"✅ {collection_name} collection created."
            )

        return chunks

    def delete_collection(self, name):
        self.client.delete_collection(name=name)

    def rename_collection(self, old_name, new_name):
        collection = self.get_collection(old_name)
        collection.modify(name=new_name)

    def reset_db(self):
        for collection_name in self.all_collections():
            self.delete_collection(collection_name)

    def all_collections(self):
        return [collection.name for collection in self.client.list_collections()]

    def embed_and_add_documents(
        self, collection_name, documents, metadatas=None, ids=None
    ):
        collection = self.get_collection(collection_name)
        collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def query_collection(
        self,
        collection_name,
        query_texts=None,
        n_results=None,
        where=None,
        where_document=None,
        include=None,
    ):
        collection = self.get_collection(collection_name)
        return collection.query(
            query_embeddings=self.embedding_function(query_texts),
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=include,
        )

    def update_collection(
            self,
            collection_name,
            ids,
            embeddings=None,
            metadatas=None,
            documents=None):
        collection = self.get_collection(collection_name)
        collection.update(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents)

    def upsert_collection(
            self,
            collection_name,
            ids,
            embeddings=None,
            metadatas=None,
            documents=None):
        collection = self.get_collection(collection_name)
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents)

    def delete_from_collection(self, collection_name, ids=None, where=None):
        collection = self.get_collection(collection_name)
        collection.delete(ids=ids, where=where)

    def reset_chromadb(self):
        self.client.reset()

    def heartbeat_chromadb(self):
        return self.client.heartbeat()
