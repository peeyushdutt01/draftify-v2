import asyncio
from collections import Counter, defaultdict

from agents.planner import planner
from agents.researcher import researcher
from agents.reranker import reranker
from agents.extractor import extractor
from agents.writer import writer
from agents.evaluator import evaluator
from agents.publisher import publisher
from helpers.state import State


async def main():

    state = State(
        user_request="Indian Independence Movement and the lesser known leaders"
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

    print("=" * 80)
    print("WRITER")
    print("=" * 80)

    writer_updates = await writer(state)
    state = state.model_copy(update=writer_updates)

    word_count = len(state.draft_article.split())
    print(f"Draft article: {word_count} words total\n")

    for section in state.plan.sections:
        section_facts = [
            f for f in state.research_facts if section in f.sections
        ]
        print(f"- {section}: {len(section_facts)} facts used")

    print("=" * 80)
    print("EVALUATOR")
    print("=" * 80)

    evaluator_updates = await evaluator(state)
    state = state.model_copy(update=evaluator_updates)

    print(f"Score: {evaluator_updates.get('score', 'N/A')}")
    print(f"Passed: {state.review_passed}\n")
    print("Review comments:")
    for comment in state.review_comments:
        print(f"- {comment}")

    print("=" * 80)
    print("PUBLISHER")
    print("=" * 80)

    publisher_updates = await publisher(state)
    state = state.model_copy(update=publisher_updates)

    print(f"Exports: {state.exports}")
    if state.errors:
        print(f"Errors: {state.errors}")

    print()
    print("-" * 80)
    print(state.draft_article)
    print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())