import asyncio
import logging

import trafilatura
from playwright.async_api import async_playwright

from helpers.state import Article, SearchResult

logger = logging.getLogger(__name__)

async def scrape(result: SearchResult)->Article | None:
    """
    Scrape a search result and return its extracted article.

    Returns None if the page cannot be scraped or no readable content
    could be extracted.
    """
    try:    
        logger.info("Scraping %s", result.url)
        html = await _fetch_html(str(result.url))

        content = _content_extractor(html)

        if not content:
            logger.warning("No readable content extracted from %s", result.url)
            return None

        return Article(
            title=result.title,
            url= result.url,
            content=content
        )
    except Exception:
        logger.exception("Failed to scrape %s", result.url)
        return None

async def scrape_many(results: list[SearchResult]) -> list[Article]:
    """
    Scrape multiple search results concurrently.

    Failed scrapes are skipped.
    """
    tasks = [
        scrape(result)
        for result in results
    ]

    articles = await asyncio.gather(*tasks)
    logger.info("Scraping complete: %d succeeded, %d failed", sum(article is not None for article in articles), sum(article is None for article in articles))

    return [article 
            for article in articles 
            if article is not None]

async def _fetch_html(url:str) -> str:
    logger.info("Fetching HTML: %s", url)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        try:
            context = await browser.new_context()

            page = await context.new_page()

            await page.goto(
                url,
                wait_until="networkidle",
                timeout=30000
            )
            await page.wait_for_timeout(1500)

            html = await page.content()
            logger.info("Fetched HTML: %s (%d bytes)", url, len(html))
            return html
        finally:
            await browser.close()

def _content_extractor(html:str) -> str|None:
    return trafilatura.extract(html)

