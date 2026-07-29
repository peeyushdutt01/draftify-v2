from ddgs import DDGS
from helpers.state import SearchSource, SearchResponse, SearchResult, SearchProvider
import arxiv

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
                await _search_social(query)
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

async def _search_social()->list[SearchResult]:
    return []



        

import asyncio

async def main():
    response = await search(
        queries=["Gemma 4"],
        sources=[SearchSource.RESEARCH],
    )

    for result in response.results:
        print(result.title)
        print(result.url)
        print(result.source)
        print(result.snippet)
        print()


if __name__ == "__main__":
    asyncio.run(main())