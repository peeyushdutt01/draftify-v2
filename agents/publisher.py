import asyncio
import os

from helpers.state import State
from tools.export import save_md_as_pdf


async def publisher(state: State):
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    safe_topic = "".join(
        c if c.isalnum() or c in (" ", "-") else ""
        for c in state.plan.topic
    ).strip().replace(" ", "_")[:60]

    output_path = os.path.join(output_dir, f"{safe_topic}.pdf")

    exports: dict[str, str] = {}
    errors: list[str] = []

    try:
        await asyncio.to_thread(save_md_as_pdf, state.draft_article, output_path)
        exports["pdf"] = output_path
    except Exception as e:
        errors.append(f"PDF export failed: {e}")

    return {
        "exports": exports,
        "errors": state.errors + errors,
        "current_step": "publishing_completed",
    }