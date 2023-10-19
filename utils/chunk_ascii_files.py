import logging
import re
from typing import List

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
    model: str = tokenizer_model,
    signal_progress_update=None,
    progress_range=(50, 60),
) -> List[str]:
    chunks = []
    lines = text.split("\n")
    total_lines = len(lines)
    for idx, line in enumerate(lines):
        if num_tokens_from_text(line, model) > max_tokens:
            line = shorten_last_list(line, max_tokens, model)

        # Report progress
        if signal_progress_update:
            progress = progress_range[0] + (
                ((idx + 1) / total_lines) * (progress_range[1] - progress_range[0])
            )
            signal_progress_update.emit(
                int(progress),
                f"File Processing: {idx + 1}/{total_lines} files ({int(progress)}%)",
            )

        chunks.append(line)
    return chunks


def split_files_to_chunks(
    files,
    max_tokens=max_embedding_tokens,
    model=tokenizer_model,
    signal_progress_update=None,
    progress_range=(40, 50),
):
    chunks = []
    total_files = len(files)
    for idx, file in enumerate(files):
        logger.info(f"processing file: {file}")
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if not text.strip():
            logger.warning(f"No text available in file: {file}")
            continue

        # Report progress
        if signal_progress_update:
            progress = progress_range[0] + (
                ((idx + 1) / total_files) * (progress_range[1] - progress_range[0])
            )
            signal_progress_update.emit(
                int(progress),
                f"File Processing: {idx + 1}/{total_files} files ({int(progress)}%)",
            )

        chunks += split_text_to_chunks(text, max_tokens, model)

    return chunks
