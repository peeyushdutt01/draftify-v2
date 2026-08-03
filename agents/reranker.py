import asyncio
import os
import re

import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer

from helpers.state import Article, Chunk, State

_CROSS_ENCODER_MODEL = os.getenv("RERANKER_CROSS_ENCODER_MODEL", "BAAI/bge-reranker-v2-m3")
_EMBEDDING_MODEL = os.getenv("RERANKER_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

_cross_encoder: CrossEncoder | None = None
_embedder: SentenceTransformer | None = None


def _get_cross_encoder() -> CrossEncoder:
    global _cross_encoder
    if _cross_encoder is None:
        _cross_encoder = CrossEncoder(_CROSS_ENCODER_MODEL)
    return _cross_encoder

def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(_EMBEDDING_MODEL)
    return _embedder

async def reranker(state: State):

    chunks = _chunk_articles(state.scraped_articles)

    selected = await _select_chunks(
        state.user_request,
        chunks,
    )

    return {
        "ranked_articles": selected,
    }

def _chunk_articles(
    articles: list[Article],
    target_words: int = 500,
    max_words: int = 700,
) -> list[Chunk]:

    chunks: list[Chunk] = []

    for article_index, article in enumerate(articles):

        paragraphs = [
            p.strip()
            for p in article.content.split("\n\n")
            if p.strip()
        ]

        current_chunk: list[str] = []
        current_words = 0
        chunk_index = 0

        for paragraph in paragraphs:

            paragraph_words = len(paragraph.split())

            if paragraph_words > max_words:

                if current_chunk:
                    chunks.append(
                        Chunk(
                            article_index=article_index,
                            chunk_index=chunk_index,
                            title=article.title,
                            url=article.url,
                            content="\n\n".join(current_chunk),
                        )
                    )
                    chunk_index += 1
                    current_chunk = []
                    current_words = 0

                sentences = re.split(r'(?<=[.!?])\s+', paragraph)

                sentence_chunk = []
                sentence_words = 0

                for sentence in sentences:
                    words = len(sentence.split())

                    if sentence_chunk and sentence_words + words > target_words:
                        chunks.append(
                            Chunk(
                                article_index=article_index,
                                chunk_index=chunk_index,
                                title=article.title,
                                url=article.url,
                                content=" ".join(sentence_chunk),
                            )
                        )
                        chunk_index += 1
                        sentence_chunk = []
                        sentence_words = 0

                    sentence_chunk.append(sentence)
                    sentence_words += words

                if sentence_chunk:
                    chunks.append(
                        Chunk(
                            article_index=article_index,
                            chunk_index=chunk_index,
                            title=article.title,
                            url=article.url,
                            content=" ".join(sentence_chunk),
                        )
                    )
                    chunk_index += 1

                continue

            # Normal paragraph-aware chunking
            if current_chunk and current_words + paragraph_words > target_words:

                chunks.append(
                    Chunk(
                        article_index=article_index,
                        chunk_index=chunk_index,
                        title=article.title,
                        url=article.url,
                        content="\n\n".join(current_chunk),
                    )
                )

                chunk_index += 1
                current_chunk = []
                current_words = 0

            current_chunk.append(paragraph)
            current_words += paragraph_words

        if current_chunk:
            chunks.append(
                Chunk(
                    article_index=article_index,
                    chunk_index=chunk_index,
                    title=article.title,
                    url=article.url,
                    content="\n\n".join(current_chunk),
                )
            )

    return chunks

async def _select_chunks(
    query: str,
    chunks: list[Chunk],
    max_chunks: int = 10,
    redundancy_threshold: float = 0.88,
    lambda_relevance: float = 0.7,
) -> list[Chunk]:

    if not chunks:
        return []

    if len(chunks) <= max_chunks:
        return chunks

    cross_encoder = _get_cross_encoder()
    embedder = _get_embedder()

    pairs = [(query, chunk.content) for chunk in chunks]
    relevance_scores = await asyncio.to_thread(cross_encoder.predict, pairs)

    embeddings = await asyncio.to_thread(
        embedder.encode,
        [chunk.content for chunk in chunks],
        normalize_embeddings=True,
    )

    order = np.argsort(relevance_scores)[::-1]  # highest relevance first
    selected_indices: list[int] = []

    for idx in order:
        if len(selected_indices) >= max_chunks:
            break

        if selected_indices:
            sims = embeddings[idx] @ embeddings[selected_indices].T
            max_sim = sims.max()
            if max_sim >= redundancy_threshold:
                continue  # too similar to something already picked, skip

        selected_indices.append(idx)

    return [chunks[i] for i in selected_indices]
