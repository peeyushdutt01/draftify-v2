import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from agents.planner import planner
from helpers.llm import get_llm
from helpers.state import ResearchSelection, SearchResult, State, SearchRequest
from prompts.researcher import RESEARCHER_PROMPT
from prompts.search import SEARCH_PROMPT
from tools.scraper import scrape_many
from tools.search import search
from tools.rerank import dedupe_results, select_for_scraping,rrf_merge
import asyncio

load_dotenv()

async def researcher(state: State):

    search_llm = (
        get_llm(
            model=os.getenv("RESEARCHER_MODEL"),
            temperature=0.1,
        )
        .with_structured_output(SearchRequest)
    )

    search_request = await search_llm.ainvoke(
        [
            SystemMessage(content=SEARCH_PROMPT),
            HumanMessage(content=state.user_request),
        ]
    )

    search_response = await search(
        queries=search_request.query,
        sources=search_request.sources,
    )

    print(f"[funnel] raw search results: {len(search_response.results)}")

    deduped = dedupe_results(search_response.results)
    print(f"[funnel] after dedupe: {len(deduped)}")

    selected = rrf_merge(deduped)
    print(f"[funnel] after RRF: {len(selected)}")

    articles = await scrape_many(selected)
    print(f"[funnel] scraped articles: {len(articles)}")

    return {
        "search_request": search_request,
        "search_results": search_response.results,
        "scraped_articles": articles,
        "current_step": "research_completed",
    }

 