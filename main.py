import asyncio
import logging

from graph import build_graph
from helpers.state import State

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("draftify.log", encoding="utf-8"),
        ],
        force=True,
    )


async def main():
    configure_logging()
    logger.info("Starting Draftify")
    graph = build_graph()
    logger.info("Graph compiled")

    initial_state = State(
        user_request=input("What should the article be about? ").strip()
    )
    logger.info("Received request: %s", initial_state.user_request)

    logger.info("Running workflow")
    final_state_dict = await graph.ainvoke(initial_state)
    final_state = State.model_validate(final_state_dict)
    logger.info("Workflow completed with step=%s", final_state.current_step)

    print("=" * 80)
    print(f"Score: {final_state_dict.get('score', 'N/A')}  Passed: {final_state.review_passed}")
    print("=" * 80)

    if final_state.review_comments:
        print("\nReview comments:")
        for comment in final_state.review_comments:
            print(f"- {comment}")

    if final_state.errors:
        print("\nErrors encountered:")
        for error in final_state.errors:
            print(f"- {error}")

    print(f"\nExports: {final_state.exports}")
    logger.info("Run finished; exports=%s errors=%d", final_state.exports, len(final_state.errors))


if __name__ == "__main__":
    asyncio.run(main())