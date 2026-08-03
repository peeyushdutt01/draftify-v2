import asyncio

from agents.planner import planner
from agents.researcher import researcher
from agents.reranker import reranker
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

    from collections import Counter
    by_article = Counter(c.article_index for c in state.ranked_articles)
    print("Chunks per article_index:", dict(by_article))

    for i, chunk in enumerate(state.ranked_articles, start=1):
        print(f"[{i}] article_index={chunk.article_index}  {chunk.title[:70]}")

if __name__ == "__main__":
    asyncio.run(main())


