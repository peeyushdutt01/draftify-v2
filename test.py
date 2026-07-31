import asyncio

from agents.planner import planner
from agents.researcher import researcher
from agents.reranker import reranker
from helpers.state import State


async def main():

    state = State(
        user_request="why did indian students went into protest"
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

    for i, chunk in enumerate(state.ranked_articles, start=1):
        print(f"[{i}] {chunk.title}")
        print("-" * 60)
        print(chunk.content[:300])
        print()


if __name__ == "__main__":
    asyncio.run(main())