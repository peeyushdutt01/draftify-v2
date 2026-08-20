import asyncio

from graph import build_graph
from helpers.state import State


async def main():
    graph = build_graph()

    initial_state = State(
        user_request=input("What should the article be about? ").strip()
    )

    final_state_dict = await graph.ainvoke(initial_state)
    final_state = State.model_validate(final_state_dict)

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


if __name__ == "__main__":
    asyncio.run(main())