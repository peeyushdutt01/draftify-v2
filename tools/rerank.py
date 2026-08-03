from difflib import SequenceMatcher
from urllib.parse import urlparse, parse_qs

from helpers.state import SearchResult

from collections import defaultdict


_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term",
    "utm_content", "ref", "fbclid", "gclid",
}


def _normalize_url(url: str) -> str:
    """Strip scheme, www, trailing slash, and tracking params so the same
    article from different links collapses to one key."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    clean_query = {
        k: v for k, v in query_params.items()
        if k not in _TRACKING_PARAMS
    }
    netloc = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/")
    query_str = "&".join(sorted(clean_query.keys()))
    return f"{netloc}{path}?{query_str}" if query_str else f"{netloc}{path}"


def _title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def dedupe_results(
    results: list[SearchResult],
    title_threshold: float = 0.85,
) -> list[SearchResult]:
    seen_urls: set[str] = set()
    deduped: list[SearchResult] = []

    for result in results:
        norm_url = _normalize_url(str(result.url))
        if norm_url in seen_urls:
            continue

        is_near_duplicate = any(
            _title_similarity(result.title, kept.title) >= title_threshold
            for kept in deduped
        )
        if is_near_duplicate:
            continue

        seen_urls.add(norm_url)
        deduped.append(result)

    return deduped


def rrf_merge(
    results: list[SearchResult],
    k: int = 60,
    top_k_per_query: int = 8,
) -> list[SearchResult]:
    """Blend results across sources within each query facet, using each
    provider's own return order as its rank. No scoring model involved."""

    by_query_source: dict[tuple[str, str], list[SearchResult]] = defaultdict(list)
    for result in results:
        by_query_source[(result.query, result.source.value)].append(result)

    scored: list[tuple[float, SearchResult]] = []
    for group in by_query_source.values():
        for rank, result in enumerate(group, start=1):
            scored.append((1 / (k + rank), result))

    by_query: dict[str, list[tuple[float, SearchResult]]] = defaultdict(list)
    for score, result in scored:
        by_query[result.query].append((score, result))

    fused: list[SearchResult] = []
    for query, group in by_query.items():
        ranked = sorted(group, key=lambda pair: pair[0], reverse=True)
        fused.extend(result for _, result in ranked[:top_k_per_query])

    return fused


def select_for_scraping(
    results: list[SearchResult],
    top_k_per_query: int = 8,
) -> list[SearchResult]:
    """Full pre-scrape selection: dedupe, then facet-balanced rank fusion.
    Replaces the old LLM-based _select_sources step entirely."""
    deduped = dedupe_results(results)
    return rrf_merge(deduped, top_k_per_query=top_k_per_query)



