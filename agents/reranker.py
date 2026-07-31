import os
import re

from dotenv import load_dotenv

from helpers.llm import get_llm
from helpers.state import Article, Chunk, ChunkSelection, State

load_dotenv()

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
) -> list[Chunk]:

    if len(chunks) <= max_chunks:
        return chunks

    formatted_chunks = []

    for i, chunk in enumerate(chunks):
        formatted_chunks.append(
            f"""
Chunk {i}

Title:
{chunk.title}

Content:
{chunk.content}
""".strip()
                    )

    prompt = f"""
        You are an expert document reranker.

        Your task is to select the BEST chunks for answering the user's query.

        User Query:
        {query}

        Rules:
        - Select AT MOST {max_chunks} chunks.
        - Choose chunks that directly answer the query.
        - Remove redundant chunks.
        - Prefer chunks containing concrete facts, numbers, explanations and examples.
        - If two chunks contain the same information, keep the better one.
        - Return ONLY the selected chunk indices.

        Chunks:

        {"\n\n------------------------\n\n".join(formatted_chunks)}
        """
    response: ChunkSelection = await (
        get_llm(
            model=os.getenv("RERANKER_MODEL"),
            temperature=0.0
        )
        .with_structured_output(ChunkSelection)
        .ainvoke(prompt)
    )

    return [
        chunks[idx]
        for idx in response.selected
        if 0 <= idx < len(chunks)
    ]

