import os

import arxiv
import praw
from ddgs import DDGS
from dotenv import load_dotenv

from helpers.state import SearchProvider, SearchResponse, SearchResult, SearchSource

load_dotenv()

async def search(
    queries: list[str],
    sources: list[SearchSource],
) -> SearchResponse:

    results: list[SearchResult] = []

    for query in queries:

        if SearchSource.WEB in sources:
            results.extend(
                _search_web(query)
            )

        if SearchSource.NEWS in sources:
            results.extend(
                _search_news(query)
            )

        if SearchSource.RESEARCH in sources:
            results.extend(
                _search_research(query)
            )

        if SearchSource.SOCIAL in sources:
            results.extend(
                _search_social(query)
            )

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
    except Exception:  # noqa: BLE001
        print("Arxiv Search Fail : ",Exception)
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

    except Exception:  # noqa: BLE001
        print("Reddit Search Fail : ",Exception)
        return results
