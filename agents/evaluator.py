import logging
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from helpers.llm import get_llm
from helpers.state import Plan, State
from prompts.evaluator import EVALUATOR_PROMPT

load_dotenv()
logger = logging.getLogger(__name__)

class EvaluationResult(BaseModel):
    review_comments : list[str]
    score : int

async def evaluator(state:State):
    logger.info("Evaluating draft (%d words)", len(state.draft_article.split()))
    evaluation = await _evaluate_content(
        plan = state.plan, 
        content = state.draft_article)
    logger.info("Evaluation complete: score=%d comments=%d", evaluation.score, len(evaluation.review_comments))

    return {
        "review_comments" : evaluation.review_comments,
        "review_passed" : evaluation.score > 7
    }



async def _evaluate_content(plan:Plan , content: str) -> EvaluationResult:
    llm = get_llm(
        model = os.getenv("EVALUATOR_MODEL"),
        temperature = 0.0,
    ).with_structured_output(EvaluationResult)

    messages = [
        SystemMessage(content=EVALUATOR_PROMPT),
        HumanMessage(content=f"""
Here is the initial plan for the Newsletter : {plan},
you are required to evaluate the content based on the given plan.
you have to provide review comments for the article draft.

here is the content : {content}""".strip()),
    ]

    response = await llm.ainvoke(messages)

    return response
    