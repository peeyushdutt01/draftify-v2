import logging
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from helpers.llm import get_llm
from helpers.state import Plan, State
from prompts.planner import PLANNER_PROMPT

load_dotenv()

PLANNER_MODEL = os.getenv("PLANNER_MODEL")
logger = logging.getLogger(__name__)

def planner(state:State):
    logger.info("Building plan for request")
    planner_llm = get_llm(
        model = PLANNER_MODEL,
        temperature = 0.8
    ).with_structured_output(Plan)
    messages = [
        SystemMessage(content=PLANNER_PROMPT),
        HumanMessage(content=state.user_request)
    ]

    plan = planner_llm.invoke(messages)
    logger.info("Plan created: %d sections, %d search queries", len(plan.sections), len(plan.search_queries))
    # state.plan = plan  #for testing
    return {
        "plan" : plan,
        "current_step" : "planning_completed"
    }

