import logging
import re
from typing import List

import chromadb
import chromadb.utils.embedding_functions as ef
import tiktoken

from usdchat.config.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

tokenizer_model = Config.TOKENIZER_MODEL
max_embedding_tokens = Config.MAX_EMBEDDING_TOKENS


def num_tokens_from_text(text: str, model: str = tokenizer_model) -> int:
    encoding = tiktoken.encoding_for_model(model)
    token_count = len(encoding.encode(text))
    return token_count


def split_long_line(
    line: str, max_tokens: int, model: str = tokenizer_model
) -> List[str]:
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(line)
    if len(tokens) <= max_tokens:
        return [line]
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i: i + max_tokens]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks


def shorten_last_list(
        line: str,
        max_tokens: int,
        model: str = tokenizer_model) -> str:
    pattern = re.compile(r"\[([^\]]+)\]")
    matches = pattern.findall(line)
    if not matches:
        split_long_line(line, max_tokens, model)
        return line
    last_match = matches[-1]
    items = last_match.split(",")
    shortened_items = items[:4] + items[-4:]
    shortened_list_str = ",".join(shortened_items)
    shortened_text = re.sub(pattern, f"[{shortened_list_str}]", line, count=1)
    return shortened_text


def split_text_to_chunks(
        text: str,
        max_tokens: int = max_embedding_tokens,
        model: str = tokenizer_model) -> List[str]:
    chunks = []
    lines = text.split("\n")
    for line in lines:
        if num_tokens_from_text(line, model) > max_tokens:
            line = shorten_last_list(line, max_tokens, model)
        chunks.append(line)
    return chunks


def split_files_to_chunks(
    files,
    max_tokens=max_embedding_tokens,
    model=tokenizer_model,
    signal_progress_update=None,
    progress_range=(60, 80),
):
    chunks = []
    total_files = len(files)
    for idx, file in enumerate(files):
        print(f"processing file: {file}")
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if not text.strip():
            logger.warning(f"No text available in file: {file}")
            continue
        chunks += split_text_to_chunks(text, max_tokens, model)

        # Report progress
        if signal_progress_update:
            progress = progress_range[0] + (
                ((idx + 1) / total_files) * (progress_range[1] - progress_range[0])
            )
            signal_progress_update.emit(
                int(progress), f"File processing progress: {int(progress)}%"
            )

    return chunks


def get_or_create_collection(client, name):
    try:
        collection = client.get_collection(name)
    except ValueError as e:
        if str(e) == f"Collection {name} does not exist.":
            embedding_function = ef.SentenceTransformerEmbeddingFunction(
                Config.EMBEDDING_MODEL
            )
            collection = client.create_collection(
                name=name,
                embedding_function=embedding_function,
                metadata={
                    "hnsw:space": "ip",
                    "hnsw:construction_ef": 30,
                    "hnsw:M": 32},
                get_or_create=True,
            )
        else:
            raise  # re-raise the exception if it's not about the collection missing
    return collection


def create_and_store_embeddings(
    files,
    db_path=Config.DB_PATH,
    embedding_model=Config.EMBEDDING_MODEL,
    signal_progress_update=None,
    progress_range=(80, 100),
):
    client = chromadb.PersistentClient(path=db_path)
    collection = get_or_create_collection(client, "stage")
    chunks = split_files_to_chunks(files)
    total_chunks = len(chunks)
    logger.info(f"Found {total_chunks} chunks.")

    # Define a batch size that is within the limits
    batch_size = 80000  # Adjust this value as needed
    for i in range(0, total_chunks, batch_size):
        batch_docs = chunks[i: i + batch_size]
        batch_ids = [f"doc_{j}" for j in range(i, i + len(batch_docs))]
        collection.add(documents=batch_docs, ids=batch_ids)

        # Report progress
        if signal_progress_update:
            progress = progress_range[0] + (
                ((i + len(batch_docs)) / total_chunks)
                * (progress_range[1] - progress_range[0])
            )
            signal_progress_update.emit(
                int(progress), f"Embedding progress: {int(progress)}%"
            )

    logger.info(f"Upserted {total_chunks} chunks.")
    if signal_progress_update:
        signal_progress_update.emit(
            progress_range[1], "Embedding completed"
        )  # Ensure this doesn't go beyond the allocated range


def reset_chromadb(db_path: str = Config.DB_PATH):
    client = chromadb.PersistentClient(path=db_path)
    client.reset()


def heartbeat_chromadb(db_path: str = Config.DB_PATH):
    client = chromadb.PersistentClient(path=db_path)
    heartbeat = client.heartbeat()
    return heartbeat
