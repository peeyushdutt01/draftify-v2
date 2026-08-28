import logging
import os

import arxiv
import praw
from ddgs import DDGS
from dotenv import load_dotenv

from helpers.state import SearchProvider, SearchResponse, SearchResult, SearchSource

load_dotenv()
logger = logging.getLogger(__name__)

async def search(
    queries: list[str],
    sources: list[SearchSource],
) -> SearchResponse:

    results: list[SearchResult] = []
    logger.info("Starting search: queries=%d sources=%s", len(queries), sources)

    for query in queries:

        if SearchSource.WEB in sources:
            found = _search_web(query)
            results.extend(found)
            logger.info("Web search '%s': %d results", query, len(found))

        if SearchSource.NEWS in sources:
            found = _search_news(query)
            results.extend(found)
            logger.info("News search '%s': %d results", query, len(found))

        if SearchSource.RESEARCH in sources:
            found = _search_research(query)
            results.extend(found)
            logger.info("Research search '%s': %d results", query, len(found))

        if SearchSource.SOCIAL in sources:
            found = _search_social(query)
            results.extend(found)
            logger.info("Social search '%s': %d results", query, len(found))

    logger.info("Search complete: %d total results", len(results))
    return SearchResponse(results=results)



def _search_web(query)->list[SearchResult]:
    results : list[SearchResult] = []
    with DDGS() as ddgs:
        response = ddgs.text(
            query,
            max_results = 10,
        )
        for item in response:
            results.append(SearchResult(
                title=item["title"],
                url=item["href"],
                snippet=item["body"],
                source=SearchSource.WEB,
                provider=SearchProvider.DDGS,
                query=query
            ))
        
    return results

def _search_news(query: str) -> list[SearchResult]:
    results: list[SearchResult] = []

    with DDGS() as ddgs:
        response = ddgs.news(
            query,
            max_results=10,
        )

        for item in response:
            results.append(
                SearchResult(
                    title=item["title"],
                    url=item["url"],
                    snippet=item["body"],
                    source=SearchSource.NEWS,
                    provider=SearchProvider.DDGS_NEWS,
                    query=query,
                )
            )

    return results

def _search_research(query: str) -> list[SearchResult]:
    results: list[SearchResult] = []
    try:

        client = arxiv.Client()

        search = arxiv.Search(
            query=query,
            max_results=10,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        for paper in client.results(search):
            results.append(
                SearchResult(
                    title=paper.title,
                    url=paper.entry_id,
                    snippet=paper.summary,
                    source=SearchSource.RESEARCH,
                    provider=SearchProvider.ARXIV,
                    query=query,
                )
            )

        return results
    except Exception:
        logger.exception("Arxiv search failed for '%s'", query)
        return results

def _search_social(query:str)->list[SearchResult]:
    results : list[SearchResult] = []
    try:

        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
        )
        for post in reddit.subreddit("all").search(query,limit = 10):
            results.append(
                SearchResult(
                    title = post.title,
                    url = post.url, 
                    snippet = post.selftext, 
                    source = SearchSource.SOCIAL, 
                    provider = SearchProvider.REDDIT, 
                    query = query,
                )
            )

        return results

    except Exception:
        logger.exception("Reddit search failed for '%s'", query)
        return results
