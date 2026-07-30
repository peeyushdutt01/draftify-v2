from helpers.state import State, SearchResult, ResearchSelection
from tools.scraper import  scrape_many
from langchain_core.messages import HumanMessage, SystemMessage
from helpers.llm import get_llm
from dotenv import load_dotenv
from prompts.researcher import RESEARCHER_PROMPT
import os

load_dotenv()

async def researcher(state: State):

    selected = await _select_sources(
        state.user_request,
        state.search_results,
    )

    articles = await scrape_many(selected)

    return {
        "articles": articles
    }



async def _select_sources(
    query: str,
    results: list[SearchResult],
    ) -> list[SearchResult]:
    researcher_llm = get_llm(
        model= os.getenv("RESEARCHER_MODEL"),
        temperature = 0.7,
    ).with_structured_output(ResearchSelection)

    formatted_results = _format_results(results)
    messages = [
        SystemMessage(content=RESEARCHER_PROMPT),
        HumanMessage(content= f"""
        research question : 
        {query}
        search results : 
        {formatted_results}
        """.strip()
        )
    ]

    response = await researcher_llm.ainvoke(messages)

    return [ results[i] 
            for i in response.selected
            if 0 <= i < len(results)]


def _format_results(results: list[SearchResult]) -> str:
    sections = []

    for index, result in enumerate(results):
        lines = [
            "=" * 50,
            f"Index: {index}",
            f"Title: {result.title}",
            f"Source: {result.source.value}",
            f"URL: {result.url}",
        ]

        if result.snippet:
            lines.append(f"Snippet: {result.snippet}")

        sections.append("\n".join(lines))

    return "\n\n".join(sections)