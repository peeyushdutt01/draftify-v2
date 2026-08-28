import logging
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from helpers.llm import get_llm
from helpers.state import Fact, State
from prompts.writer import WRITER_PROMPT

load_dotenv()
logger = logging.getLogger(__name__)


async def writer(state: State):
    plan = state.plan
    facts_by_section = _group_facts_by_section(state.research_facts, plan.sections)

    draft_parts: list[str] = []
    logger.info("Writing %d sections", len(plan.sections))

    for section in plan.sections:
        section_facts = facts_by_section.get(section, [])
        logger.info("Writing section '%s' with %d facts", section, len(section_facts))
        section_text = await _write_section(
            topic=plan.topic,
            audience=plan.audience,
            medium=plan.medium,
            section=section,
            facts=section_facts,
            previous_section=draft_parts[-1] if draft_parts else None,
        )
        draft_parts.append(f"## {section}\n\n{section_text}")

    return {
        "draft_article": "\n\n".join(draft_parts),
        "current_step": "writing_completed",
    }


def _group_facts_by_section(
    facts: list[Fact],
    sections: list[str],
) -> dict[str, list[Fact]]:
    grouped: dict[str, list[Fact]] = {section: [] for section in sections}
    for fact in facts:
        for section in fact.sections:
            if section in grouped:
                grouped[section].append(fact)
    return grouped


def _format_facts(facts: list[Fact]) -> str:
    if not facts:
        return (
            "(No sourced facts available for this section. Write briefly from "
            "general knowledge, and do not fabricate specific statistics or claims.)"
        )
    return "\n".join(
        f"{i}. {fact.text} (Source: {fact.source_title})"
        for i, fact in enumerate(facts, start=1)
    )


async def _write_section(
    topic: str,
    audience: str,
    medium: str,
    section: str,
    facts: list[Fact],
    previous_section: str | None,
) -> str:

    writer_llm = get_llm(
        model=os.getenv("WRITER_MODEL"),
        temperature=0.4,
    )

    continuity_context = (
        previous_section if previous_section else "(This is the opening section.)"
    )

    messages = [
        SystemMessage(content=WRITER_PROMPT),
        HumanMessage(content=f"""
Topic: {topic}
Audience: {audience}
Medium: {medium}

Section to write: {section}

Previous section (for tone and flow only — do not repeat its content):
{continuity_context}

Facts available for this section:
{_format_facts(facts)}

Write only the content for this section. Stay grounded in the facts listed
above — do not introduce specific claims, numbers, or examples that aren't
supported by them.
""".strip())
    ]

    response = await writer_llm.ainvoke(messages)
    return response.content