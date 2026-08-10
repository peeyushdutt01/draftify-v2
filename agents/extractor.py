import asyncio
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from helpers.llm import get_llm
from helpers.state import Chunk, ExtractedFact, Fact, Plan, State
from prompts.extractor import EXTRACTOR_PROMPT

load_dotenv()

_MAX_CONCURRENT_CALLS = 3 


class ChunkExtraction(BaseModel):
    chunk_ref: int  
    facts: list[ExtractedFact]


class BatchFacts(BaseModel):
    chunks: list[ChunkExtraction]


async def extractor(state: State):
    facts = await _extract_facts(state.plan, state.ranked_articles)

    return {
        "research_facts": facts,
        "current_step": "extraction_completed",
    }


async def _extract_facts(
    plan: Plan,
    chunks: list[Chunk],
    batch_size: int = 4,
) -> list[Fact]:

    if not chunks:
        return []

    batches = [
        chunks[i:i + batch_size]
        for i in range(0, len(chunks), batch_size)
    ]

    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_CALLS)

    async def _bounded_extract(batch: list[Chunk]) -> list[Fact]:
        async with semaphore:
            return await _extract_batch(plan, batch)

    results = await asyncio.gather(*(_bounded_extract(b) for b in batches))

    return [fact for batch_facts in results for fact in batch_facts]


async def _extract_batch(plan: Plan, batch: list[Chunk]) -> list[Fact]:

    llm = get_llm(
        model=os.getenv("EXTRACTOR_MODEL"),
        temperature=0.0,
    ).with_structured_output(BatchFacts)

    messages = [
        SystemMessage(content=EXTRACTOR_PROMPT),
        HumanMessage(content=f"""
Topic: {plan.topic}

Valid sections (use ONLY these exact names when tagging a fact):
{", ".join(plan.sections)}

Extract 2-4 standalone, atomic facts from EACH chunk below that support one
or more of the sections above. Skip chunks with nothing genuinely relevant.
Tag each fact with the section(s) it supports.

{_format_batch(batch)}
""".strip()),
    ]

    response: BatchFacts = await llm.ainvoke(messages)

    facts: list[Fact] = []
    valid_sections = set(plan.sections)

    for chunk_extraction in response.chunks:
        if not (0 <= chunk_extraction.chunk_ref < len(batch)):
            continue  # guard against a hallucinated index

        chunk = batch[chunk_extraction.chunk_ref]

        for extracted in chunk_extraction.facts:
            sections = [s for s in extracted.sections if s in valid_sections]

            facts.append(
                Fact(
                    text=extracted.text,
                    sections=sections,
                    source_title=chunk.title,
                    source_url=chunk.url,
                    article_index=chunk.article_index,
                    chunk_index=chunk.chunk_index,
                )
            )

    return facts


def _format_batch(batch: list[Chunk]) -> str:
    parts = []
    for i, chunk in enumerate(batch):
        parts.append(f"""
Chunk Ref: {i}
Title: {chunk.title}
Content:
{chunk.content}
""".strip())
    return "\n\n" + "\n\n---\n\n".join(parts)