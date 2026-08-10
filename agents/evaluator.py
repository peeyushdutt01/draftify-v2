from helpers.state import State, Plan
from helpers.llm import get_llm
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from prompts.evaluator import EVALUATOR_PROMPT


load_dotenv()

class EvaluationResult(BaseModel):
    review_comments : list[str]
    score : int

async def evaluator(state:State):
    evaluation = await _evaluate_content(
        plan = state.plan, 
        content = state.draft_article)
    

    return {
        "review_comments" : evaluation.review_comments,
        "review_passed" : evaluation.score > 7
    }



async def _evaluate_content(plan:Plan , content: str) -> EvaluationResult:
    llm = get_llm(
        model = os.getenv("EVALUATION_MODEL"),
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
    