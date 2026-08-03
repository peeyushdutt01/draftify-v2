import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from helpers.llm import get_llm
from helpers.state import Plan, State
from prompts.planner import PLANNER_PROMPT

load_dotenv()

PLANNER_MODEL = os.getenv("PLANNER_MODEL")

def planner(state:State):
    planner_llm = get_llm(
        model = PLANNER_MODEL,
        temperature = 0.8
    ).with_structured_output(Plan)
    messages = [
        SystemMessage(content=PLANNER_PROMPT),
        HumanMessage(content=state.user_request)
    ]

    plan = planner_llm.invoke(messages)
    # state.plan = plan  #for testing
    return {
        "plan" : plan,
        "current_step" : "planning_completed"
    }

