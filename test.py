import asyncio
from collections import Counter, defaultdict

from agents.planner import planner
from agents.researcher import researcher
from agents.reranker import reranker
from agents.extractor import extractor
from helpers.state import State


async def main():

    state = State(
        user_request="gengis khan and how he became the ancestor of most of the today's present humans"
    )

    print("=" * 80)
    print("PLANNER")
    print("=" * 80)

    planner_updates = planner(state)
    state = state.model_copy(update=planner_updates)

    print(state.plan)

    print("=" * 80)
    print("RESEARCHER")
    print("=" * 80)

    researcher_updates = await researcher(state)
    state = state.model_copy(update=researcher_updates)

    print(f"Articles scraped: {len(state.scraped_articles)}\n")

    for article in state.scraped_articles:
        print(f"- {article.title}")

    print("=" * 80)
    print("RERANKER")
    print("=" * 80)

    reranker_updates = await reranker(state)
    state = state.model_copy(update=reranker_updates)

    print(f"Selected chunks: {len(state.ranked_articles)}\n")

    by_article = Counter(c.article_index for c in state.ranked_articles)
    print("Chunks per article_index:", dict(by_article))

    for i, chunk in enumerate(state.ranked_articles, start=1):
        print(f"[{i}] article_index={chunk.article_index}  {chunk.title[:70]}")

    print("=" * 80)
    print("EXTRACTOR")
    print("=" * 80)

    extractor_updates = await extractor(state)
    state = state.model_copy(update=extractor_updates)

    print(f"Facts extracted: {len(state.research_facts)}\n")

    orphaned = [f for f in state.research_facts if not f.sections]
    print(f"Orphaned facts (no valid section tag): {len(orphaned)}\n")

    by_section: dict[str, int] = defaultdict(int)
    for fact in state.research_facts:
        for section in fact.sections:
            by_section[section] += 1
    print("Facts per section:", dict(by_section))

    by_source = Counter(f.source_title for f in state.research_facts)
    print("Facts per source:", dict(by_source))
    print()

    for i, fact in enumerate(state.research_facts, start=1):
        print(f"[{i}] {fact.text}")
        print(f"    sections={fact.sections}  source={fact.source_title[:50]}")
        print()


if __name__ == "__main__":
    asyncio.run(main())