import logging
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from helpers.llm import get_llm
from helpers.state import SearchRequest, State
from prompts.search import SEARCH_PROMPT
from tools.rerank import dedupe_results, rrf_merge
from tools.scraper import scrape_many
from tools.search import search

load_dotenv()
logger = logging.getLogger(__name__)

async def researcher(state: State):
    logger.info("Generating search requests")

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
    logger.info("Searching %d queries across sources=%s", len(search_request.query), search_request.sources)

    search_response = await search(
        queries=search_request.query,
        sources=search_request.sources,
    )

    logger.info("Raw search results: %d", len(search_response.results))

    deduped = dedupe_results(search_response.results)
    logger.info("After dedupe: %d", len(deduped))

    selected = rrf_merge(deduped)
    logger.info("After RRF selection: %d", len(selected))

    articles = await scrape_many(selected)
    logger.info("Scraped articles: %d", len(articles))

    return {
        "search_request": search_request,
        "search_results": search_response.results,
        "scraped_articles": articles,
        "current_step": "research_completed",
    }

 